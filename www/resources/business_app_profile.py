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
    def post(self, uid=None):
        logging.info('Client requested for business profile.')
        body = request.get_json(force=True)

        try:
            validate_json(body, business_app_schema)
            # validate_json(body, business_signup_schema)
            logging.info('Client requested for business_app with uid: \n{}'.format(pprint.pformat(body)))
            return self.graph_db.find_business(body.get('uid'))
        except JsonValidationException as exc:
            msg = {'messages': exc.message}
            logging.debug(msg)
            logging.info('Oh Snap')
            return msg, 400
