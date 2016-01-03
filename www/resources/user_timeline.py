from operator import itemgetter
from flask_restful.reqparse import RequestParser
from www.resources.config import configs
from www.resources.utilities.helpers import filter_general_document_db_record

__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www import oauth2, db_helper


class UserTimeline(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, target_uid, uid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')

        if before and after and before < after:
            msg = {'message': '`before` argument must be greater than or equal to `after`.'}
            logging.debug(msg)
            return msg, 400

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        each_limit = limit/2

        try:
            followings_list = self.graph_db.find_user_followings(target_uid, users=True, businesses=False)
            followings_list_uids = [x.get('user').get('uid') for x in followings_list]
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followings for this user.'}
            logging.debug(msg)
            return msg, 204

        try:
            friends_reviews = self.doc_db.find_doc(None, None, 'business_reviews', limit=each_limit, conditions={'uid': {'$in': followings_list_uids}}, sort_key='timestamp', sort_direction=-1)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            friends_reviews = []

        except Exception as exc:
            return {'message': 'internal_server_error'}, 500

        try:
            friends_checkins = self.doc_db.find_doc(None, None, 'checkins', limit=each_limit, conditions={'uid': {'$in': followings_list_uids}}, sort_key='timestamp', sort_direction=-1)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            friends_checkins = []

        except Exception as exc:
            return {'message': 'internal_server_error'}, 500

        response_list = friends_reviews + friends_checkins
        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return filter_general_document_db_record(response_list)
