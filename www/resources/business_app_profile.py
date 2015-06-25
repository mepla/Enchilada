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
