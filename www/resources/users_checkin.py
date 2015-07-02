__author__ = 'Naja'
from flask_restful import Resource
from www.authentication.oauth2 import OAuth2Provider
from www.databases.factories import DatabaseFactory
from www.databases.database_drivers import DatabaseFindError, DatabaseRecordNotFound
import logging


class UsersCheckin(Resource):

    def __init__(self):
        super(UsersCheckin, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @OAuth2Provider.check_access_token
    def get(self, user_id, uid):
        logging.debug('Client requested to retrieve user info for user_id: {}'.format(user_id))

        try:
            users_checkin = self.graph_db.find_single_user_checkins(user_id)
            return users_checkin
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'User does not exist or does not have any checkins.'}
            logging.debug(msg)
            return msg, 404

