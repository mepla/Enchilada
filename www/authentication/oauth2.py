__author__ = 'Mepla'

import time
import logging
from uuid import uuid4
from functools import wraps
import re

from flask import request

from www.databases.factories import DatabaseFactory
from www.databases.database_drivers import DatabaseFindError

max_ttl = 604800


class ClientNotAuthorized(Exception):
    pass

class ClientDoesNotExist(Exception):
    pass

class ClientWithWrongScopes(Exception):
    pass

class AccessToResourceDenied(Exception):
    pass

class OAuth2Provider(object):
    def __init__(self):
        self.auth_db = DatabaseFactory().get_database_driver('document/auth')

    def client_id_check(self, client_id, client_secret, scope):
        try:
            existing_client = self.auth_db.find_doc('client_id', client_id, 'clients')
            if not existing_client.get('client_secret') == client_secret:
                raise ClientNotAuthorized()

            scopes = set(scope.split(' '))
            existing_client_scopes = set(existing_client.get('scope').split(' '))

            if not scopes.issubset(existing_client_scopes):
                raise ClientWithWrongScopes()

        except DatabaseFindError as exc:
            raise ClientDoesNotExist()

    def generate_access_token(self, uid, client_id, scope, ttl=max_ttl):
        access_token = uuid4().hex
        refresh_token = uuid4().hex

        try:
            existing_client = self.auth_db.find_doc('client_id', client_id, 'clients')
        except DatabaseFindError as exc:
            raise ClientDoesNotExist()

        doc = {'access_token': access_token, 'refresh_token': refresh_token, 'expires_in': ttl, 'token_type': 'Bearer',
               'scope': scope, 'uid': uid, 'client_id': client_id, 'issue_date': time.time()}
        self.auth_db.save(doc, 'tokens')

        return {'access_token': access_token, 'refresh_token': refresh_token, 'expires_in': ttl, 'token_type': 'Bearer', 'scope': scope}

    def refresh_access_token(self, refresh_token):
        try:
            doc = self.auth_db.find_doc('refresh_token', refresh_token, 'tokens')
        except DatabaseFindError as exc:
            msg = {'message': 'You refresh token does not exit.'}
            logging.error(msg)
            return msg, 400

        if doc:
            uid = doc.get('uid')
            c_id = doc.get('client_id')
            scope = doc.get('scope')
            ttl = doc.get('expires_in')
            return self.generate_access_token(uid, c_id, scope, ttl)

        else:
            msg = {'message': 'You refresh token does not exit.'}
            logging.error(msg)
            return msg, 400

    def check_access_token(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            auth = request.headers.get('Authorization')
            client_id = request.headers.get('x-echo-client-id')

            if not client_id:
                msg = {'message': 'Your request must have a \'x-echo-client-id\' header set to your client ID.'}
                logging.error(msg)
                return msg, 401

            logging.debug('Authorizing client with ID and secret.')

            try:
                (token_type, token) = auth.split(' ')
            except Exception as exc:
                msg = {'message': 'Your HTTP Authorization header must be set to \'Bearer YOUR_ACCESS_TOKEN\'.'}
                logging.error(msg)
                return msg, 401

            logging.debug('Authorizing resource owner with access token: {}'.format(token_type + token))

            token_doc = self.auth_db.find_doc('access_token', token, 'tokens')
            if token_doc:
                if not client_id == token_doc.get('client_id'):
                    msg = {'message': 'Your client_id does not match with your access token.'}
                    logging.error(msg)
                    return msg, 401

                if time.time() - token_doc.get('issue_date') > token_doc.get('expires_in'):
                    msg = {'message': 'Your access token is expired, please refresh it using your refresh token.'}
                    logging.error(msg)
                    return msg, 401
            else:
                msg = {'message': 'Your access token does not exist.'}
                logging.error(msg)
                return msg, 401

            logging.info('Resource owner authenticated successfully. client_id: {}  uid: {}'.format(token_doc.get('client_id'), token_doc.get('uid')))

            path = request.path.replace('self', token_doc.get('uid'))

            try:
                self.check_allowed_scopes(request.method.lower() + ' ' + path.lower(), token_doc.get('scope'), token_doc.get('uid'))
            except DatabaseFindError as exc:
                msg = {'message': 'Could not find scope in defined scopes: {}'.format(token_doc.get('scope'))}
                logging.error(msg)
                return msg, 500

            except AccessToResourceDenied as exc:
                msg = {'message': 'Your access token has a scope of `{}` which is not capable of requesting resource at {} with method {}'.format(token_doc.get('scope'), path, request.method.upper())}
                logging.error(msg)
                return msg, 403

            if path != request.path and 'user_id' in kwargs:
                kwargs['user_id'] = token_doc.get('uid')

            return f(*args, **dict(kwargs.items() + {'uid': token_doc.get('uid')}.items()))

        return wrapper

    def check_allowed_scopes(self, method_uri, scope, uid):
        logging.debug('Checking scope authorization for request: {}'.format(method_uri))

        scope_doc = self.auth_db.find_doc('doc', 'all_scopes', 'scopes')

        if not scope_doc:
            raise DatabaseFindError

        all_scopes = scope_doc['scopes'][scope]
        regex_list = []
        for i in range(0, len(all_scopes)):
            reg_scope = all_scopes[i].replace('{self}', uid)
            regex_list.append(reg_scope)

        regex = '|'.join(regex_list)

        result = re.match(regex, method_uri)

        if not result:
            raise AccessToResourceDenied()

        logging.debug('User ({}) is authorized to request resource ({})'.format(uid, method_uri))

