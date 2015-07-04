__author__ = 'Naja'

from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_app_schema, business_signup_schema
from flask import request
import logging
import pprint
from www.authentication.oauth2 import OAuth2Provider

class BusinessProfile(Resource):
    def __init__(self):
        super(BusinessProfile, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @OAuth2Provider.check_access_token
    def get(self, uid, bid):
        logging.info('Client requested for business profile.')
        return self.graph_db.find_business(bid)


class BusinessCategory(Resource):
    def __init__(self):
        super(BusinessCategory, self).__init__()
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @OAuth2Provider.check_access_token
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
