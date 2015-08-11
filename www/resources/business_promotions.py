__author__ = 'Mepla'

from flask_restful.reqparse import RequestParser
from www.config import configs
import logging
import time

from flask_restful import Resource
from flask import request

from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, create_promotion_schema
from www import oauth2
from www.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseSaveError, \
    DatabaseFindError
from www.utilities.helpers import filter_general_document_db_record
from www.utilities.helpers import uuid_with_prefix


class BusinessPromotions(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    def get(self, bid, uid=None):
        try:
            promotions = self.doc_db.find_doc('bid', bid, 'business_promotions', limit=100)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_promotions.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204

        return filter_general_document_db_record(promotions)

    def post(self, bid, uid=None):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, create_promotion_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        data['bid'] = bid
        data['pid'] = uuid_with_prefix('pid')

        try:
            self.doc_db.save(data, 'business_promotions')
            return filter_general_document_db_record(data), 201
        except DatabaseSaveError as exc:
            msg = {'message': 'Your promotion could not be saved. This is an internal error.'}
            logging.error(msg)
            return msg, 500


class BusinessPromotion(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    def get(self, bid, pid, uid=None):
        try:
            doc = self.doc_db.find_doc('pid', pid, 'business_promotions', 1)
            return filter_general_document_db_record(doc)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error(msg)
            return msg, 500
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Business Promotion could not be found.'}
            logging.error(msg)
            return msg, 404

    def delete(self, bid, pid, uid=None):
        result = self.doc_db.delete('business_promotions', {'pid': pid})

        if result > 0:
            return None, 204
        else:
            msg = {'message': 'There is no promotion with pid ({}).'.format(pid)}
            logging.error(msg)
            return msg, 404
