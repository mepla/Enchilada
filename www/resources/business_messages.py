import time
from www.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult

__author__ = 'Mepla'


from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, message_schema
from flask import request
from www.resources.helpers import filter_general_document_db_record

import logging
from www import oauth2
import uuid


class BusinessMessages(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    def get(self, uid, bid):
        try:
            messages = self.doc_db.find_doc('bid', bid, 'business_messages', limit=10)

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

        doc = {'data': data, 'timestamp': time.time(), 'uid': uid, 'bid': bid, 'mid': uuid.uuid4().hex, 'seen': False}

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