from www.resources.authentication.password_management import PasswordManager
from www.resources.config import configs

__author__ = 'Mepla'

import logging

from flask import request
from flask_restful import Resource

from www.resources.json_schemas import validate_json, JsonValidationException, patch_schema, user_put_schema, \
    forgot_password_schema, change_forgotten_password_schema
from www.resources.databases.factories import DatabaseFactory
from www.resources.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound, DocumentNotUpdated, \
    DatabaseEmptyResult
from www import oauth2, db_helper
from www.resources.utilities.helpers import Patch, filter_user_info, uuid_with_prefix, utc_now_timestamp, \
    filter_general_document_db_record
from itsdangerous import URLSafeSerializer


class ForgotPassword(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/auth')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    def post(self):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, forgot_password_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        email = data.get('email').lower()
        try:
            existing_user = self.graph_db.find_single_user('email', email)
        except DatabaseRecordNotFound:
            return {'message': 'User not found'}, 400
        except DatabaseFindError:
            return {'message': 'Internal Server Error'}, 500

        expiration = configs.get('POLICIES').get('forgot_password_expiration')
        token_document = {'token': uuid_with_prefix('fpt'), 'uid': existing_user.get('uid'), 'created': utc_now_timestamp(), 'expires_in': expiration}
        self.doc_db.save(token_document, 'forgot_tokens')
        key = configs.get('HMAC_KEY')
        s = URLSafeSerializer(key)
        token_document = filter_general_document_db_record(token_document)
        token_str = s.dumps(token_document)
        return {'token': token_str}


class ChangeForgottenPassword(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/auth')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    def post(self):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, change_forgotten_password_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        new_pass = data.get('new_password')
        token_hmac = data.get('token')

        key = configs.get('HMAC_KEY')
        s = URLSafeSerializer(key)

        try:
            token_data = s.loads(token_hmac)
        except Exception as exc:
            logging.error('Can not decode HMAC: {}'.format(exc))
            return {'message': 'malformed_data'}

        token = token_data.get('token')
        uid = token_data.get('uid')

        try:
            existing_token_doc = self.doc_db.find_doc('uid', uid, 'forgot_tokens', 1, {'token': token})
            created_timestamp = existing_token_doc.get('created')
            expires_in = existing_token_doc.get('expires_in')
        except DatabaseRecordNotFound as exc:
            return {'message': 'Your token is either wrong or expired.'}, 400

        except DatabaseEmptyResult as exc:
            return {'message': 'Internal Server Error'}, 500

        if utc_now_timestamp() >= created_timestamp + expires_in:
            return {'message': 'Your token is expired.'}, 400

        try:
            existing_user = self.graph_db.find_single_user('uid', uid)
        except DatabaseRecordNotFound:
            return {'message': 'User not found'}, 400
        except DatabaseFindError:
            return {'message': 'Internal Server Error'}, 500

        new_hash = PasswordManager.hash_password(new_pass, uid, existing_user['email'])
        existing_user['password'] = new_hash
        self.graph_db.update(existing_user)
        self.doc_db.delete('forgot_tokens', {'token': token})

        return
