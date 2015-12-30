__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www import oauth2, db_helper


class UserFollowings(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, target_uid, uid=None):
        try:
            existing_user = self.graph_db.find_single_user('uid', target_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The user you tried to get following of does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            response = self.graph_db.find_user_followings(target_uid, users=True, businesses=False)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followings for this user.'}
            logging.debug(msg)
            return msg, 204

        return response
