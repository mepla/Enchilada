from flask_restful.reqparse import RequestParser

from www.resources.config import configs

__author__ = 'Mepla'

import logging
import time

from flask_restful import Resource
from flask import request

from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, survey_result_schema
from www import oauth2, db_helper
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseSaveError, \
    DatabaseFindError
from www.resources.utilities.helpers import filter_general_document_db_record, utc_now_timestamp
from www.resources.utilities.helpers import uuid_with_prefix


class BusinessSurveyResults(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, uid, bid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, survey_result_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            existing_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The business you tried to create promotion for does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        data['uid'] = uid
        data['bid'] = bid
        data['timestamp'] = utc_now_timestamp()
        data['srid'] = uuid_with_prefix('srid')

        try:
            self.doc_db.save(data, 'business_survey_results')
            return None, 201
        except DatabaseSaveError as exc:
            msg = {'message': 'Your survey could not be saved. This is an internal error.'}
            logging.error(msg)
            return msg, 500

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid):
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

        conditions = {}

        if before:
            conditions['timestamp'] = {'$lt': before}

        if after:
            if conditions.get('timestamp'):
                conditions['timestamp']['$gt'] = after
            else:
                conditions['timestamp'] = {'$gt': after}

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        try:
            surveys = self.doc_db.find_doc('bid', bid, 'business_survey_results', limit=limit, conditions=conditions, sort_key='timestamp', sort_direction=-1)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_survey_templates.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no survey templates for this business.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are no survey templates for this business.'}
            logging.error(msg)
            return msg, 204

        return filter_general_document_db_record(surveys)


class BusinessSurveyResult(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, survey_id):
        try:
            doc = self.doc_db.find_doc('srid', survey_id, 'business_survey_results', 1)
            return filter_general_document_db_record(doc)
        except DatabaseFindError as exc:
            msg = {'message': 'Survey does not exist.'}
            logging.error(msg)
            return msg, 404
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Survey does not exist.'}
            logging.error(msg)
            return msg, 204

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def delete(self, bid, survey_id, uid=None):
        result = self.doc_db.delete('business_survey_results', {'srid': survey_id})

        if result > 0:
            return None, 204
        else:
            msg = {'message': 'There is no survey result with survey_id ({}).'.format(survey_id)}
            logging.error(msg)
            return msg, 404


class BusinessSurveyTemplates(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid):
        try:
            result = self.doc_db.find_doc('bid', bid, 'business_survey_templates', 100)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_survey_templates.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no survey templates for this business.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are no survey templates for this business.'}
            logging.error(msg)
            return msg, 204

        api_result = []
        for single_template in result:
            api_result.append(filter_business_survey_template(single_template))

        return api_result

    def post(self):
        pass


class BusinessSurveyTemplate(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, survey_id):
        try:
            if survey_id == 'active_survey':
                doc = self.doc_db.find_doc('bid', bid, 'business_survey_templates', 1, conditions={'active': True})
            else:
                doc = self.doc_db.find_doc('stid', survey_id, 'business_survey_templates', 1)
            return filter_general_document_db_record(doc)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error(msg)
            return msg, 500
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Survey template could not be found.'}
            logging.error(msg)
            return msg, 404

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def put(self):
        pass

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def delete(self, bid, survey_id, uid=None):
        result = self.doc_db.delete('business_survey_templates', {'stid': survey_id})

        if result > 0:
            return None, 204
        else:
            msg = {'message': 'There is no Survey template with survey_id ({}).'.format(survey_id)}
            logging.error(msg)
            return msg, 404


def filter_business_survey_template(template):
    return template
