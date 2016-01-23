from www.resources.notifications.notification_manager import NotificationManager
from www.resources.utilities.helpers import utc_now_timestamp, uuid_with_prefix, filter_general_document_db_record

__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.factories import DatabaseFactory
from www import oauth2, db_helper
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseFindError


class CheckIn(Resource):
    def __init__(self):
        super(CheckIn, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.notification_manager = NotificationManager()

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, bid, uid):
        logging.info('Client requested for checkin.')

        try:
            existing_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to checkin to does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            checkin_doc = {'uid': uid, 'bid': bid, 'timestamp': utc_now_timestamp(), 'ciid': uuid_with_prefix('ciid')}
            self.doc_db.save(checkin_doc, 'checkins')
        except Exception as exc:
            logging.error('Could not checkin user ({}) in business ({}): {}'.format(uid, bid, exc))
            return {'message': 'internal_server_error'}, 500

        try:
            relation = self.graph_db.checkin_user(bid, uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The business you tried to check into does not exist.'}
            logging.debug(msg)
            return msg, 400

        return filter_general_document_db_record(checkin_doc)

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, bid):
        try:
            response = self.graph_db.checkins_for_business(bid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no check_ins for this business.'}
            logging.debug(msg)
            return msg, 204

        return response
