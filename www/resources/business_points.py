from flask_restful.reqparse import RequestParser
from www.resources.accounting.accountant import Accountant

from www.resources.config import configs

__author__ = 'Mepla'

import logging

from flask_restful import Resource
from flask import request

from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, review_schema
from www.resources.utilities.helpers import filter_general_document_db_record, utc_now_timestamp
from www.resources.utilities.helpers import uuid_with_prefix
from www import oauth2


class BusinessBalance(Resource):
    def __init__(self):
        self._accountant = Accountant()

    @oauth2.check_access_token
    def get(self, uid, bid):
        try:
            result = self._accountant.get_balance(uid, bid)
            return result
        except DatabaseFindError as exc:
            return {'message': 'Internal server error'}, 500
