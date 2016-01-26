from operator import itemgetter
from flask_restful.reqparse import RequestParser
from www.resources.config import configs
from www.resources.utilities.helpers import filter_general_document_db_record, convert_str_query_string_to_bool, \
    filter_user_info

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
        parser.add_argument('include_user_info', type=bool, help='`include_user_info` argument must be a boolean.')
        parser.add_argument('include_business_info', type=bool, help='`include_business_info` argument must be a boolean.')

        args = parser.parse_args()

        conditions = {}

        include_user_info = convert_str_query_string_to_bool(args.get('include_user_info'))
        include_business_info = convert_str_query_string_to_bool(args.get('include_business_info'))

        before = args.get('before')
        after = args.get('after')

        if before and after and before < after:
            msg = {'message': '`before` argument must be greater than or equal to `after`.'}
            logging.debug(msg)
            return msg, 400

        if before:
            conditions['timestamp'] = {'$lt': before}

        if after:
            if conditions.get('timestamp'):
                conditions['timestamp']['$gt'] = after
            else:
                conditions['timestamp'] = {'$gt': after}

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        try:
            followings_list = self.graph_db.find_user_followings(target_uid, users=True, businesses=False)

            all_followings_dict = {}
            for user in followings_list:
                user_uid = (user.get('user').get('uid'))
                all_followings_dict[user_uid] = filter_user_info(user.get('user'))

            conditions['uid'] = {'$in': all_followings_dict.keys()}

        except DatabaseEmptyResult:
            msg = {'message': 'There is no followings for this user.'}
            logging.debug(msg)
            return msg, 204

        try:
            friends_reviews = self.doc_db.find_doc(None, None, 'business_reviews', limit=limit,
                                                   conditions=conditions,
                                                   sort_key='timestamp', sort_direction=-1, force_array_return=True)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            friends_reviews = []

        except Exception as exc:
            return {'message': 'internal_server_error'}, 500

        try:
            friends_checkins = self.doc_db.find_doc(None, None, 'checkins', limit=limit,
                                                    conditions=conditions,
                                                    sort_key='timestamp', sort_direction=-1, force_array_return=True)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            friends_checkins = []

        except Exception as exc:
            return {'message': 'internal_server_error'}, 500

        response_list = friends_reviews + friends_checkins
        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        response_list = response_list[0:limit]

        if include_user_info or include_business_info:
            businesses_data = {}
            users_data = {}
            for item in response_list:
                if include_user_info:
                    uid = item.get('uid')
                    if uid:
                        existing_user = users_data.get(uid)
                        if not existing_user:
                            try:
                                result = self.doc_db.find_doc('uid', uid, 'user')
                                if result:
                                    result = filter_user_info(result)
                                    users_data[uid] = result
                                    existing_user = result
                            except:
                                pass

                        item['user'] = existing_user

                if include_business_info:
                    bid = item.get('bid')
                    if bid:
                        existing_biz = businesses_data.get(bid)
                        if not existing_biz:
                            try:
                                result = self.doc_db.find_doc('bid', bid, 'business')
                                if result:
                                    result = self.filter_business_info_for_timeline(result)
                                    businesses_data[bid] = result
                                    existing_biz = result
                            except:
                                pass

                        item['business'] = existing_biz

        return filter_general_document_db_record(response_list)

    def filter_business_info_for_timeline(self, business_info):
        filtered_info = {}
        if 'name' in business_info:
            filtered_info['name'] = business_info['name']
        if 'address' in business_info:
            filtered_info['address'] = business_info['address']
        if 'hrbid' in business_info:
            filtered_info['hrbid'] = business_info['hrbid']
        if 'gallery' in business_info:
            filtered_info['gallery'] = business_info['gallery']
        return filtered_info
