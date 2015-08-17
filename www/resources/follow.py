__author__ = 'Mepla'

from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_app_schema, business_signup_schema
from flask import request
import logging
from www import oauth2
from www.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult


class Follow(Resource):
    def __init__(self):
        super(Follow, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def post(self, business_or_user_id, uid):
