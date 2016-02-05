from operator import itemgetter
from flask_restful.reqparse import RequestParser
from www.resources.utilities.helpers import filter_user_info, convert_str_query_string_to_bool

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
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, target_uid, uid=None):

        parser = RequestParser()
        parser.add_argument('include_business', type=bool, help='`include_business` argument must be a boolean.')
        args = parser.parse_args()
        include_business = convert_str_query_string_to_bool(args.get('include_business'))

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
            neo_result = self.graph_db.find_user_followings(target_uid, users=True, businesses=include_business)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followings for this user.'}
            logging.debug(msg)
            return msg, 204

        if len(neo_result) == 0:
            return '', 204

        following_uids = []
        following_bids = []
        for res in neo_result:
            uid = res.get('following').get('uid')
            bid = res.get('following').get('bid')
            if uid:
                following_uids.append(uid)
            elif bid:
                following_bids.append(bid)

        user_conditions = {'uid': {'$in': following_uids}}
        mongo_user_result = self.doc_db.find_doc(None, None, 'user', 10000, user_conditions)
        if include_business:
            biz_conditions = {'bid': {'$in': following_bids}}
            mongo_biz_result = self.doc_db.find_doc(None, None, 'business', 10000, biz_conditions)
            mongo_result = mongo_user_result + mongo_biz_result
        else:
            mongo_result = mongo_user_result
        mongo_dict_result = {}
        for result in mongo_result:
            if 'uid' in result:
                mongo_dict_result[result.get('uid')] = result
            elif 'bid' in result:
                mongo_dict_result[result.get('bid')] = result

        final_result = []

        for single_res in neo_result:
            if 'uid' in single_res.get('following'):
                uid = single_res.get('following').get('uid')
                final_result.append({'timestamp': single_res.get('timestamp'), 'user': mongo_dict_result.get(uid)})
            elif 'bid' in single_res.get('following'):
                bid = single_res.get('following').get('bid')
                final_result.append({'timestamp': single_res.get('timestamp'), 'business': mongo_dict_result.get(bid)})

        return final_result
