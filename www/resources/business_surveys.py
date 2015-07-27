__author__ = 'Mepla'

import logging
import time

from flask_restful import Resource
from flask import request

from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, survey_result_schema
from www import oauth2
from www.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseSaveError, \
    DatabaseFindError
from www.utilities.helpers import filter_general_document_db_record
from www.utilities.helpers import uuid_with_prefix


class BusinessSurveyResults(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
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

        data['uid'] = uid
        data['bid'] = bid
        data['timestamp'] = time.time()
        data['srid'] = uuid_with_prefix('srid')

        try:
            self.doc_db.save(data, 'business_survey_results')
            return None, 201
        except DatabaseSaveError as exc:
            msg = {'message': 'Your survey could not be saved. This is an internal error.'}
            logging.error(msg)
            return msg, 500

    def get(self, bid):
        try:
            result = self.doc_db.find_doc('bid', bid, 'business_survey_results', 100)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_survey_templates.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no survey templates for this business.'}
            logging.error(msg)
            return msg, 204


class BusinessSurveyResult(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    def get(self, bid, survey_id):
        try:
            doc = self.doc_db.find_doc('srid', survey_id, 'business_survey_results', 1)
            return filter_general_document_db_record(doc)
        except DatabaseFindError as exc:
            msg = {'message': 'Survey does not exist.'}
            logging.error(msg)
            return msg, 404


class BusinessSurveyTemplates(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

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

        api_result = []
        for single_template in result:
            api_result.append(filter_business_survey_template(single_template))

        return api_result

    def post(self):
        pass


class BusinessSurveyTemplate(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

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

    def put(self):
        pass

    def delete(self):
        pass


def filter_business_survey_template(template):
    return template
