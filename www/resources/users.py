from flask_restful.reqparse import RequestParser
from www.resources.authentication.password_management import PasswordManager

__author__ = 'Mepla'

import logging

from flask import request
from flask_restful import Resource

from www.resources.json_schemas import validate_json, JsonValidationException, patch_schema, user_put_schema, \
    change_normal_password_schema
from www.resources.databases.factories import DatabaseFactory
from www.resources.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound, DocumentNotUpdated, \
    DatabaseEmptyResult
from www import oauth2, db_helper
from www.resources.utilities.helpers import Patch, filter_user_info


# /users
class Users(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid=None):
        parser = RequestParser()
        parser.add_argument('name', type=str, help='`name` argument must be a string.')
        parser.add_argument('email', type=str, help='`country` argument must be a string.')

        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('sort_by', type=str, help='`sort_by` argument must be a string.')

        args = parser.parse_args()

        name = args.get('name')
        email = args.get('email')

        conditions = {}

        if name:
            uids = self.doc_db.find_users_with_concatenated_name(name)
            conditions['uid'] = {'$in': uids}

        if email:
            conditions['email'] = email

        if len(conditions) < 1:
            msg = {'message': 'You can not request to find a user without any query strings.'}
            logging.debug(msg)
            return msg, 400

        try:
            users = self.doc_db.find_doc(None, None, 'user', conditions=conditions, limit=30)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for users.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are users with this search critieria.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are users with this search critieria.'}
            logging.error(msg)
            return msg, 204

        return filter_user_info(users)


# /users/{user_id}
class User(Resource):
    read_only_fields = ['email', 'uid', 'udid', 'password', "metrics", "hruid", "user_type", "birth_date", "echo_number", "gender", "phone"]

    def __init__(self):
        super(User, self).__init__()
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, user_id, uid):
        logging.debug('Client requested to retrieve user info for user_id: {}'.format(user_id))
        print('PATH: {} user_id: {}  uid: {}'.format(request.path, user_id, uid))
        try:
            existing_user = self.doc_db.find_doc('uid', user_id, 'user')
            return filter_user_info(existing_user)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying doc database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'User does not exist.'}
            logging.debug(msg)
            return msg, 404

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def put(self, user_id, uid):

        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, user_put_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        logging.debug('Client requested to update (PUT) user info for user_id: {}'.format(user_id))

        try:
            existing_user = self.doc_db.find_doc('uid', user_id, 'user')
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'User does not exist.'}
            logging.debug(msg)
            return msg, 404

        for key in data.keys():
            if key not in self.read_only_fields:
                existing_user[key] = data[key]

        try:
            result = self.doc_db.replace_a_doc('uid', user_id, 'user', existing_user)
            return filter_user_info(result), 200
        except DocumentNotUpdated:
            msg = {'message': 'User was not updated. Please check your inputs and try again.'}
            logging.error(msg)
            return msg, 400

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def patch(self, user_id, uid):

        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, patch_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        logging.debug('Client requested to update (PATCH) user info for user_id: {}'.format(user_id))

        try:
            existing_user = self.graph_db.find_single_user('uid', user_id)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'User does not exist.'}
            logging.debug(msg)
            return msg, 404

        try:
            existing_user = Patch.patch_doc(data, existing_user, self.read_only_fields)
        except:
            pass

        try:
            self.graph_db.update(existing_user)
            return existing_user, 200
        except DocumentNotUpdated as exc:
            logging.error('Document could not be updated because it was not fetched before update.')
            msg = {'message': 'Internal server error'}
            return msg, 500


class UserChangePassword(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, uid, target_uid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, change_normal_password_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        new_pass = data.get('new_password')
        old_pass = data.get('old_password')

        try:
            existing_user = self.doc_db.find_doc('uid', uid, 'user')
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Your username and password combination is not correct.'}
            logging.error(msg)
            return msg, 401

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error'}
            logging.error(msg)
            return msg, 500

        if existing_user:
            if PasswordManager.compare_passwords(old_pass, existing_user['password'], existing_user['uid']):
                new_hash = PasswordManager.hash_password(new_pass, target_uid)
                self.doc_db.update('uid', uid, 'user', {"$set": {'password': new_hash}})
            else:
                msg = {'message': 'Your old password is not correct.'}
                return msg, 401
        else:
            msg = {'message': 'Your username and password combination is not correct.'}
            return msg, 401
