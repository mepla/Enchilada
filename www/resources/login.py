
__author__ = 'Mepla'

import logging

from base64 import b64decode
from flask import request, jsonify
from flask_restful.reqparse import RequestParser
from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.databases.database_drivers import DatabaseFindError
from www import auth, oauth2
from www.authentication.password_management import PasswordManager
from www.authentication.oauth2 import ClientNotAuthorized, ClientDoesNotExist
from www.resources.json_schemas import login_schema, validate_json, JsonValidationException


class Login(Resource):
    def __init__(self):
        pass

    def post(self):
        arg_parser = RequestParser()
        arg_parser.add_argument('grant_type', type=str, help='Your request must contain a \'grant_type\' query string. Please check the documentation.', required=True)
        args = arg_parser.parse_args()
        if args['grant_type'] == 'password':
            try:
                authorization = request.headers.get('Authorization')
                (auth_type, auth_base64) = authorization.split(' ')
                (client_id, client_secret) = b64decode(auth_base64).split(':')
            except Exception as exc:
                msg = {'message': 'Your HTTP Authorization header must be set to Basic HTTP authentication of your client_id and client_secret.'}
                logging.error(msg)
                return msg, 401

            if 'scope' not in request.headers:
                msg = {'message': 'Your HTTP headers must have a \'scope\' parameter which is a space separated list of needed scopes.'}
                logging.error(msg)
                return msg, 401

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

            try:
                data = request.get_json(force=True)
            except Exception as exc:
                msg = {'msg': 'Your JSON is invalid.'}
                logging.error(msg)
                return msg, 400

            try:
                validate_json(data, login_schema)
            except JsonValidationException as exc:
                msg = {'message': exc.message}
                return msg, 400

            username = data.get('username')
            password = data.get('password')

            graph_db = DatabaseFactory().get_database_driver('graph')
            try:
                existing_user = graph_db.find_single_user('email', username)
            except DatabaseFindError as exc:
                msg = {'message': 'Internal server error'}, 500
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

        else:
            pass
