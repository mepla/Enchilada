__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.factories import DatabaseFactory
from www import oauth2
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseFindError


class CheckIn(Resource):
    def __init__(self):
        super(CheckIn, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def post(self, bid, uid):
        logging.info('Client requested for checkin.')

        try:
            existing_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to create promotion for does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            relation = self.graph_db.checkin_user(bid, uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The business you tried to check into does not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation

    @oauth2.check_access_token
    def get(self, uid, bid):
        try:
            response = self.graph_db.checkins_for_business(bid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no check_ins for this business.'}
            logging.debug(msg)
            return msg, 204

        return response
