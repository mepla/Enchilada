__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www import oauth2, db_helper


class BusinessFollowers(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
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
    @db_helper.handle_aliases
    def post(self, bid, uid):
        try:
            existing_business = self.doc_db.find_doc('bid', bid, 'business')
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to get followers of does not exist.'}
            logging.debug(msg)
            return msg, 404

        try:
            relation = self.graph_db.follow(uid, bid)
            metrics = existing_business.get('metrics')
            metrics['followers_count'] += 1
            self.doc_db.update('bid', bid, 'business', {'$set': {'metrics': metrics}})

        except DatabaseRecordNotFound:
            msg = {'message': 'The business you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation
