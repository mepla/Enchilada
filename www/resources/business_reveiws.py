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
from www.resources.utilities.helpers import filter_general_document_db_record
from www.resources.utilities.helpers import uuid_with_prefix
from www import oauth2


class BusinessReviews(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def get(self, uid, bid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('status', type=str, help='`status` argument must be a string')
        parser.add_argument('rating', type=float, help='`rating` argument must be a float.')
        parser.add_argument('return_count', type=bool, help='`return_count` argument must be a boolean.')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')

        if before and after and before < after:
            msg = {'message': '`before` argument must be greater than or equal to `after`.'}
            logging.debug(msg)
            return msg, 400

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

        return_count = args.get('return_count')

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
            if return_count:
                count = self.doc_db.find_count('bid', bid, 'business_reviews', conditions)
                return {'count': count}
            else:
                reviews = self.doc_db.find_doc('bid', bid, 'business_reviews', limit=limit, conditions=conditions, sort_key='timestamp', sort_direction=-1)
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

        doc = {'data': data, 'timestamp': time.time(), 'uid': uid, 'bid': bid, 'rid': uuid_with_prefix('rid')}

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

            new_average = float(reviews_average * reviews_count + rating) / float(reviews_count + 1)
            existing_business['reviews']['average_rating'] = new_average
            existing_business['reviews']['count'] = reviews_count + 1

        try:
            self.doc_db.update(existing_business, 'bid', bid, 'business')
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
