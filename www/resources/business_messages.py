from werkzeug.exceptions import BadRequest
from www.config import configs

__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request

from www.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.utilities.helpers import uuid_with_prefix
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, message_schema
from www.utilities.helpers import filter_general_document_db_record
from www import oauth2


class BusinessMessages(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    def get(self, uid, bid):
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

        conditions = {}

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
            messages = self.doc_db.find_doc('bid', bid, 'business_messages', limit=limit, conditions=conditions, sort_key='timestamp', sort_direction=-1)

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The information you requested is not found'}
            logging.info(msg)
            return msg, 404

        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no messages.'}
            logging.info(msg)
            return msg, 204

        return filter_general_document_db_record(messages)

    @oauth2.check_access_token
    def post(self, uid, bid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, message_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        doc = {'data': data, 'timestamp': time.time(), 'uid': uid, 'bid': bid, 'mid': uuid_with_prefix('mid'), 'seen': False}

        try:
            self.doc_db.save(doc, 'business_messages')
        except DatabaseSaveError as exc:
            msg = {'message': 'Your changes may have been done partially or not at all.'}
            logging.error(msg)
            return msg, 500

        return None, 201


class BusinessMessage(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    def get(self, uid, bid, mid):
        try:
            message = self.doc_db.find_doc('mid', mid, 'business_messages', 1)

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The information you requested is not found'}
            logging.info(msg)
            return msg, 404

        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no messages.'}
            logging.info(msg)
            return msg, 204

        return filter_general_document_db_record(message)
