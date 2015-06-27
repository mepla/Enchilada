__author__ = 'Naja'

from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_app_schema, business_signup_schema
from flask import request
import logging
from www.authentication.oauth2 import OAuth2Provider
from www.databases.database_drivers import DatabaseRecordNotFound

class CheckIn(Resource):
    def __init__(self):
        super(CheckIn, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @OAuth2Provider.check_access_token
    def post(self, bid, uid):
        logging.info('Client requested for checkin.')
        try:
            data = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, business_app_schema)
            logging.info('Client requested for sign up with payload: {}'.format(data))
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.debug(msg)
            return msg, 400

        try:
            relation = self.graph_db.checkin_user(bid, uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The business to tried to check in doe not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation
