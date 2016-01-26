from flask_restful.reqparse import RequestParser

from www.resources.config import configs

__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask import request

from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, review_schema
from www.resources.utilities.helpers import filter_general_document_db_record, utc_now_timestamp, filter_user_info, \
    convert_str_query_string_to_bool
from www.resources.utilities.helpers import uuid_with_prefix
from www import oauth2, db_helper


class BusinessReviews(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, bid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('sort_by', type=str, help='`sort_by` argument must be a string.')
        parser.add_argument('sort_order', type=str, help='`sort_order` argument must be a string.')
        parser.add_argument('status', type=str, help='`status` argument must be a string')
        parser.add_argument('rating', type=float, help='`rating` argument must be a float.')
        parser.add_argument('return_count', type=bool, help='`return_count` argument must be a boolean.')
        parser.add_argument('return_friends', type=bool, help='`return_friends` argument must be a boolean.')
        parser.add_argument('include_user_info', type=bool, help='`include_user_info` argument must be a boolean.')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')

        if before and after and before < after:
            msg = {'message': '`before` argument must be greater than or equal to `after`.'}
            logging.debug(msg)
            return msg, 400

        sort_by = args.get('sort_by')
        if not sort_by:
            sort_by = 'timestamp'

        if sort_by not in ['timestamp', 'rating']:
            msg = {'message': '`sort_by` argument must either `timestamp` or `rating`.'}
            logging.debug(msg)
            return msg, 400

        if sort_by == 'rating':
            sort_by = 'data.rating'

        sort_order = args.get('sort_order')
        if not sort_order:
            sort_order = 'descending'

        if sort_order not in ['ascending', 'descending']:
            msg = {'message': '`sort_order` argument must either `ascending` or `descending`.'}
            logging.debug(msg)
            return msg, 400

        if sort_order == 'ascending':
            sort_order = 1
        else:
            sort_order = -1

        status = args.get('status')
        if not status:
            status = 'accepted'

        if status == 'all':
            conditions = {}
        else:
            conditions = {'status': status}

        rating = args.get('rating')
        if rating:
            conditions['data'] = {'rating': rating}

        return_count = convert_str_query_string_to_bool(args.get('return_count'))

        # TODO: They syntax of querying should not be exposed to this layer.
        if before:
            conditions['timestamp'] = {'$lt': before}

        if after:
            if conditions.get('timestamp'):
                conditions['timestamp']['$gt'] = after
            else:
                conditions['timestamp'] = {'$gt': after}

        return_friends = convert_str_query_string_to_bool(args.get('return_friends'))
        if return_friends:
            try:
                result = self.graph_db.find_user_followings(uid, users=True, businesses=False)
            except (DatabaseRecordNotFound, DatabaseEmptyResult):
                if return_count:
                    return {'count': 0}
                else:
                    return []
            following_uids = [str(following_user.get('user').get('uid')) for following_user in result]
            conditions['uid'] = {'$in': following_uids}

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        include_user_info = convert_str_query_string_to_bool(args.get('include_user_info'))
        try:
            if return_count:
                count = self.doc_db.find_count('bid', bid, 'business_reviews', conditions)
                return {'count': count}
            else:
                reviews = self.doc_db.find_doc('bid', bid, 'business_reviews', limit=limit, conditions=conditions, sort_key=sort_by, sort_direction=sort_order)
                if include_user_info:
                    for review in reviews:
                        review_uid = review.get('uid')
                        try:
                            existing_user = self.graph_db.find_single_user('uid', review_uid)
                            review['user'] = filter_user_info(existing_user)
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

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, uid, bid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, review_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            existing_business = self.doc_db.find_doc('bid', bid, 'business', limit=1)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to create promotion for does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        doc = {'data': data, 'timestamp': utc_now_timestamp(), 'uid': uid, 'bid': bid, 'rid': uuid_with_prefix('rid'), "chosen_count": 0}

        min_acceptatble_rating = configs.get("POLICIES").get('reviews').get('lowest_acceptable_rating')
        rating = data.get('rating')
        if rating <= min_acceptatble_rating:
            doc['status'] = 'needs_acceptance'
        else:
            doc['status'] = 'accepted'
            try:
                reviews_count = existing_business.get('reviews').get('count')
            except Exception as exc:
                existing_business['reviews'] = {'count': 0, 'rating_average': 0}
                reviews_count = self.doc_db.find_count('bid', bid, 'business_reviews', conditions={'status': 'accepted'})

            try:
                reviews_average = existing_business.get('reviews').get('average_rating')
            except Exception as exc:
                logging.fatal('There was not a rating_average in business document (There really should be one).')
                reviews_average = 0

            new_average = round(float(reviews_average * reviews_count + rating) / float(reviews_count + 1), 2)
            existing_business['reviews']['average_rating'] = new_average
            existing_business['reviews']['count'] = reviews_count + 1

        try:
            if doc['status'] == 'accepted':
                self.doc_db.update('bid', bid, 'business', {'$set': {'reviews': {'average_rating': new_average}, 'reviews': {'count': reviews_count+1}}})
            self.doc_db.save(doc, 'business_reviews')
        except DatabaseSaveError as exc:
            msg = {'message': 'Your changes may have been done partially or not at all.'}
            logging.error(msg)
            return msg, 500

        return None, 201


class BusinessReview(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, bid, rid):
        try:
            message = self.doc_db.find_doc('rid', rid, 'business_reviews', 1)

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

        return filter_general_document_db_record(message)


class BusinessReviewsSummary(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, uid=None):
        return_doc = {'0.5': 0, '1': 0, '1.5': 0, '2': 0, '2.5': 0, '3': 0, '3.5': 0, '4': 0, '4.5': 0, '5': 0}

        parser = RequestParser()
        parser.add_argument('latest', type=str, help='`latest` argument must be a boolean.')
        parser.add_argument('jssafe', type=str, help='`jssafe` argument must be a boolean.')
        args = parser.parse_args()

        jssafe = convert_str_query_string_to_bool(args.get('jssafe'))
        latest = convert_str_query_string_to_bool(args.get('latest'))

        try:
            if latest:
                limit = configs.get('POLICIES').get('reviews').get('latest_count')
                reviews = self.doc_db.find_doc('bid', bid, 'business_reviews', limit=limit, conditions={'status': 'accepted'}, sort_key='timestamp', sort_direction=-1)
                for review in reviews:
                    rating = review.get('data').get('rating')
                    if rating % 1 == 0:
                        rating = str(int(rating))
                    else:
                        rating = str(rating)
                    return_doc[rating] += 1
            else:
                for i in range(1, 11):
                    key = float(i)/float(2)
                    count = self.doc_db.find_count('bid', bid, 'business_reviews', conditions={'status': 'accepted', 'data': {'rating': key}})
                    if key % 1 == 0:
                        key = str(int(key))
                    else:
                        key = str(key)
                    return_doc[key] = count

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

        if jssafe:
            safe_return_doc = {}
            for key, value in return_doc.items():
                safe_key = 'f' + key.replace('.', 'p')
                safe_return_doc[safe_key] = value
            return_doc = safe_return_doc

        return return_doc
