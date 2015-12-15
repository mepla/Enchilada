__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www import oauth2


class UserFollowers(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    # @oauth2.check_access_token
    def get(self, target_uid, uid=None):
        try:
            existing_user = self.graph_db.find_single_user('uid', target_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The user you tried to get followers of does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            response = self.graph_db.find_user_followers(target_uid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followers for this user.'}
            logging.debug(msg)
            return msg, 204

        return response

    @oauth2.check_access_token
    def post(self, target_uid, uid):
        try:
            relation = self.graph_db.follow(target_uid, uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The user you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation
