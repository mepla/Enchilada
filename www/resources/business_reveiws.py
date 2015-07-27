__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask import request

from www.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, review_schema
from www.utilities.helpers import filter_general_document_db_record
from www.utilities.helpers import uuid_with_prefix
from www import oauth2


class BusinessReviews(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    def get(self, uid, bid):
        try:
            reviews = self.doc_db.find_doc('bid', bid, 'business_reviews', limit=10)

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

        return filter_general_document_db_record(reviews)

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

        doc = {'data': data, 'timestamp': time.time(), 'uid': uid, 'bid': bid, 'rid': uuid_with_prefix('rid')}

        try:
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
