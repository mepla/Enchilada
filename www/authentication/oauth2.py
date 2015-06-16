__author__ = 'Mepla'

import time
import logging
from uuid import uuid4
from functools import wraps

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

    def generate_access_token(self, uid, client_id, scope, ttl=7200):
        access_token = uuid4().hex
        refresh_token = uuid4().hex

        try:
            existing_client = self.auth_db.find_doc('client_id', client_id, 'clients')
        except DatabaseFindError as exc:
            raise ClientDoesNotExist()

        doc = {'access_token': access_token, 'refresh_token': refresh_token, 'expires_in': ttl, 'token_type': 'Bearer',
               'scope': scope, 'uid': uid, 'client_id': client_id, 'type': 'tokens', 'issue_date': time.time()}
        self.auth_db.save(doc)

        return {'access_token': access_token, 'refresh_token': refresh_token, 'expires_in': ttl, 'token_type': 'Bearer', 'scope': scope}

    def check_access_token(self, f):
        @wraps
        def wrapper(*args, **kwargs):

            auth = request.headers.get('Authorization')
            client_id = request.headers.get('x-echo-client-id')

            if not client_id:
                msg = {'message': 'Your request must have a \'x-echo-client-id\' header set to your client ID.'}
                logging.error(msg)
                return msg, 401

            try:
                (token_type, token) = auth.split(' ')
            except Exception as exc:
                msg = {'message': 'Your HTTP Authorization header must be set to \'Bearer YOUR_ACCESS_TOKEN\'.'}
                logging.error(msg)
                return msg, 401

            doc = self.auth_db['tokens'].find_doc('access_token', token)
            if doc:
                if not client_id == doc.get('client_id'):
                    raise ClientNotAuthorized()
            else:
                raise ClientNotAuthorized()

            return f(*args, **dict(kwargs.items() + {'uid': doc.get('uid')}.items()))

        return wrapper
