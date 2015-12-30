from www.resources.config import configs

__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request

from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.utilities.helpers import uuid_with_prefix, utc_now_timestamp
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, message_schema
from www.resources.utilities.helpers import filter_general_document_db_record
from www import oauth2, db_helper


class BusinessFAQ(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, bid):
        try:
            faq = self.doc_db.find_doc('bid', bid, 'business_faq', limit=1)

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The information you requested is not found'}
            logging.info(msg)
            return msg, 404

        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no faq.'}
            logging.info(msg)
            return msg, 204

        return filter_general_document_db_record(faq)
