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


class UserReviews(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    # /users/<string:target_uid>/reviews
    def get(self, target_uid, uid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('include_business_info', type=bool, help='`include_business_info` argument must be a boolean.')

        args = parser.parse_args()

        conditions = {}

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

        conditions['status'] = 'accepted'
        try:
            reviews = self.doc_db.find_doc('uid', target_uid, 'business_reviews', limit=limit, conditions=conditions)
            if include_business_info:
                business_infos = {}
                for review in reviews:
                    review_bid = review.get('bid')
                    try:
                        existing_biz = business_infos.get(review_bid)
                        if not existing_biz:
                            existing_biz = self.doc_db.find_doc('bid', review_bid, doc_type='business', limit=1)
                            business_infos[review_bid] = self.filter_business_info_for_reviews(existing_biz)
                        review['business'] = business_infos.get(review_bid)
                    except Exception as exc:
                        logging.error('Could not fetch user info in Business Reviews: {}'.format(exc))

            return filter_general_document_db_record(reviews)

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The information you requested is not found'}
            logging.info(msg)
            return msg, 404

        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no reviews.'}
            logging.info(msg)
            return msg, 204

    def filter_business_info_for_reviews(self, business_info):
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