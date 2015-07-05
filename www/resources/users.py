__author__ = 'Mepla'

import logging
from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound
from www import oauth2
from filtering_results import filter_user_info

# /users
class Users(Resource):
    def __init__(self):
        pass

# /users/{user_id}
class User(Resource):
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


