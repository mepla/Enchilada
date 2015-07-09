__author__ = 'Mepla'

from flask import request
from www.resources.json_schemas import validate_json, JsonValidationException, patch_schema, signup_schema, \
    user_put_schema
import logging
from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound, DocumentNotUpdated
from www import oauth2
from helpers import filter_user_info, Patch

# /users
class Users(Resource):
    def __init__(self):
        pass

# /users/{user_id}
class User(Resource):
    read_only_fields = ['email', 'uid', 'udid', 'password']

    def __init__(self):
        super(User, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def get(self, user_id, uid):
        logging.debug('Client requested to retrieve user info for user_id: {}'.format(user_id))

        try:
            existing_user = self.graph_db.find_single_user('uid', user_id)
            return filter_user_info(existing_user)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'User does not exist.'}
            logging.debug(msg)
            return msg, 404

    @oauth2.check_access_token
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

        for key in data.keys():
            if key not in self.read_only_fields:
                existing_user[key] = data[key]

        try:
            result = self.graph_db.update(existing_user)
            return filter_user_info(result), 200
        except DocumentNotUpdated:
            msg = {'message': 'User was not updated. Please check your inputs and try again.'}
            logging.error(msg)
            return msg, 400

    @oauth2.check_access_token
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
