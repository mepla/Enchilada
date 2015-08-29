__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request

from www.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.databases.factories import DatabaseFactory
from www import oauth2


class BusinessFollowers(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    # @oauth2.check_access_token
    def get(self, bid, uid=None):
        try:
            existing_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to get followers of does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            response = self.graph_db.find_business_followers(bid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no check_ins for this business.'}
            logging.debug(msg)
            return msg, 204

        return response

    @oauth2.check_access_token
    def post(self, bid, uid):
        try:
            relation = self.graph_db.follow(bid, uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The business you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation
