from cement.core import exc
from www.databases.database_drivers import DatabaseSaveError

__author__ = 'Naja'

from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_app_schema, business_signup_schema, \
    business_category_add_single_schema
from flask import request
from www.resources.helpers import filter_general_document_db_record

import logging
from www import oauth2
import uuid


class BusinessProfile(Resource):
    def __init__(self):
        super(BusinessProfile, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def get(self, uid, bid):
        logging.info('Client requested for business profile.')
        return self.graph_db.find_business(bid)


class BusinessCategory(Resource):
    def __init__(self):
        super(BusinessCategory, self).__init__()
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    def get(self, uid):
        logging.debug('Client requested Business Categories.')
        resp = self.doc_db.find_doc(None, None, 'business_categories', 100)

        if resp:
            logging.debug('Business Categories returned: {}'.format(resp))
            return resp, 200
        else:
            msg = {'Message': 'The collection you asked for is empty'}
            logging.error(msg)
            return msg, 204

    def post(self):
        logging.debug('Client requested to create a business category.')
        data = request.get_json(force=True)

        try:
            if isinstance(data, dict):
                validate_json(data, business_category_add_single_schema)
                data['bcid'] = uuid.uuid4().hex
                self.doc_db.save(data, 'business_categories')
                return filter_general_document_db_record(data), 200

            elif isinstance(data, list):
                for doc in data:
                    validate_json(doc, business_category_add_single_schema)
                    doc['bcid'] = uuid.uuid4().hex

                self.doc_db.save(data, 'business_categories', True)
                return filter_general_document_db_record(data), 200

        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        except DatabaseSaveError as exc:
            msg = {'message': 'Your changes may have been done partially or not at all.'}
            logging.error(msg)
            return msg, 500
