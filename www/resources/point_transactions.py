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
from www import oauth2, db_helper


class PointTransactions(Resource):
    def __init__(self):
        self._accountant = Accountant()

    @oauth2.check_access_token
    @db_helper.handle_aliases
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

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        try:
            result = self._accountant.get_point_transactions(uid, bid, limit=limit, before=before, after=after)
            return result
        except DatabaseFindError as exc:
            return {'message': 'Internal server error'}, 500
