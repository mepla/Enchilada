
__author__ = 'Mepla'

import logging
from base64 import b64decode

from flask import request, jsonify
from flask_restful.reqparse import RequestParser
from flask_restful import Resource

from www.resources.databases.factories import DatabaseFactory
from www.resources.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound
from www import oauth2
from www.resources.authentication.password_management import PasswordManager
from www.resources.authentication.oauth2 import ClientNotAuthorized, ClientDoesNotExist, WrongRefreshToken
from www.resources.json_schemas import login_schema, validate_json, JsonValidationException


class Login(Resource):
    def __init__(self):
        pass

    def post(self):
        arg_parser = RequestParser()
        arg_parser.add_argument('grant_type', type=str, help='Your request must contain a \'grant_type\' query string. Please check the documentation.', required=True)
        arg_parser.add_argument('refresh_token', type=str, required=False)
        # TODO: This should be deleted and scope should only be read from headers.
        arg_parser.add_argument('scope', type=str, required=False)
        args = arg_parser.parse_args()
        try:
            authorization = request.headers.get('Authorization')
            (auth_type, auth_base64) = authorization.split(' ')
            (client_id, client_secret) = b64decode(auth_base64).split(':')
        except Exception as exc:
            msg = {'message': 'Your HTTP Authorization header must be set to Basic HTTP authentication of your client_id and client_secret.'}
            logging.error(msg)
            return msg, 401

        if 'scope' not in request.headers:
            scope = args.get('scope')
            if scope is not None:
                pass
            else:
                msg = {'message': 'Your HTTP headers must have a \'scope\' parameter which is a space separated list of needed scopes.'}
                logging.error(msg)
                return msg, 401
        else:
            scope = request.headers.get('scope')

        try:
            oauth2.client_id_check(client_id, client_secret, scope)
        except ClientNotAuthorized as exc:
            msg = {'message': 'You are not an authorized client.'}
            logging.error(msg)
            return msg, 401
        except ClientDoesNotExist:
            msg = {'message': 'Your username and password combination is not correct.'}
            logging.error(msg)
            return msg, 401

        if args['grant_type'] == 'password':
            try:
                data = request.get_json(force=True, silent=False)
            except Exception as exc:
                msg = {'msg': 'Your JSON is invalid.'}
                logging.error(msg)
                return msg, 400

            try:
                validate_json(data, login_schema)
            except JsonValidationException as exc:
                msg = {'message': exc.message}
                logging.error(msg)
                return msg, 400

            username = data.get('username')
            username = username.lower()
            password = data.get('password')

            doc_db = DatabaseFactory().get_database_driver('document/docs')
            try:
                existing_user = doc_db.find_doc('email', username, 'user')
            except DatabaseRecordNotFound as exc:
                msg = {'message': 'Your username and password combination is not correct.'}
                logging.error(msg)
                return msg, 401

            except DatabaseFindError as exc:
                msg = {'message': 'Internal server error'}
                logging.error(msg)
                return msg, 500

            if existing_user:
                if PasswordManager.compare_passwords(password, existing_user['password'], existing_user['uid'], existing_user['email']):
                    access_token_response = oauth2.generate_access_token(existing_user['uid'], client_id, scope)
                    return jsonify(access_token_response)
                else:
                    msg = {'message': 'Your username and password combination is not correct.'}
                    return msg, 401
            else:
                msg = {'message': 'Your username and password combination is not correct.'}
                return msg, 401

        elif args['grant_type'] == 'refresh_token':
            refresh_token = args.get('refresh_token')
            try:
                return oauth2.refresh_access_token(refresh_token)
            except WrongRefreshToken:
                msg = 'Your refresh token either does not exist or has expired.'
                logging.error(msg)
                return {'message': msg}, 400
            except Exception as exc:
                msg = 'Internal Server Error'
                logging.error('{}: {}'.format(msg, exc))
                return {'message': msg}, 500
