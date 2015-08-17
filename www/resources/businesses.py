from www.databases.database_drivers import DatabaseSaveError, DatabaseFindError, DatabaseRecordNotFound, \
    DocumentNotUpdated, DatabaseEmptyResult

__author__ = 'Mepla'

from flask_restful import Resource
from www.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_update_schema, business_signup_schema, \
    business_category_add_single_schema, add_admin_for_business_schema
from flask import request
from www.utilities.helpers import filter_general_document_db_record, filter_user_info

import logging
from www import oauth2
from www.utilities.helpers import uuid_with_prefix


class Businesses(Resource):
    def __init__(self):
        super(Businesses, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    # @oauth2.check_access_token
    def post(self, uid=None):
        logging.debug('Client requested to create a business.')

        try:
            body = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(body, business_signup_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            return self.graph_db.create_new_business(**body)
        except Exception as exc:
            msg = {'message': 'Internal server error'}
            logging.error(exc, msg)
            return msg


class BusinessProfile(Resource):
    def __init__(self):
        super(BusinessProfile, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def get(self, uid, bid):
        logging.debug('Client requested for business profile.')
        try:
            existing_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error'}
            logging.error(exc, msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Business does not exist with this bid.'}
            logging.debug(msg)
            return msg, 404

        return existing_business

    # @oauth2.check_access_token
    def put(self, bid, uid=None):
        logging.debug('Client requested to update a business.')

        try:
            body = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(body, business_update_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            exisiting_business = self.graph_db.find_single_business('bid', bid)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error'}
            logging.error(exc, msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Business does not exist with this bid.'}
            logging.debug(msg)
            return msg, 404

        except Exception as exc:
            logging.error(exc)

        for key in body.keys():
            if key in exisiting_business:
                if exisiting_business[key] != body[key]:
                    exisiting_business[key] = body[key]
        try:
            self.graph_db.update(exisiting_business)
        except DocumentNotUpdated as exc:
            msg = {'message': 'Business was not updated. Please check your inputs and try again.'}
            logging.error(exc, msg)
            return msg, 400

        return exisiting_business


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

        try:
            data = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            if isinstance(data, dict):
                validate_json(data, business_category_add_single_schema)
                data['bcid'] = uuid_with_prefix('bcid')
                self.doc_db.save(data, 'business_categories')
                return filter_general_document_db_record(data), 200

            elif isinstance(data, list):
                for doc in data:
                    validate_json(doc, business_category_add_single_schema)
                    doc['bcid'] = uuid_with_prefix('bcid')

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


class BusinessAdmins(Resource):
    def __init__(self):
        super(BusinessAdmins, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def post(self, uid, bid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, add_admin_for_business_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            existing_user = self.graph_db.find_single_user('uid', data['uid'])
        except DatabaseRecordNotFound as exc:
            logging.error('The uid you tried to add as admin does not exist bid: {}  uid: {}'.format(bid, data['uid']))
            msg = {'message': 'Internal server error'}
            return msg, 400
        except DatabaseFindError as exc:
            logging.error('Could add uid add admin for business, uid find error: bid:{} uid: {}'.format(bid, data['uid']))
            msg = {'message': 'Internal server error'}
            return msg, 500

        responsible = existing_user.get('responsible_for')

        if responsible and responsible.find(bid) >=0:
            should_update = False
        else:
            should_update = True
            responsible = ''

        if should_update:
            existing_user['responsible_for'] = responsible + ' ' + bid
            try:
                user = self.graph_db.update(existing_user)
            except DocumentNotUpdated as exc:
                logging.error('Could not add business admin: bid: {}  uid: {}'.format(bid, data['uid']))
                msg = {'message': 'Internal server error'}
                return msg, 500
        else:
            user = existing_user

        return filter_user_info(user), 200

    @oauth2.check_access_token
    def get(self, bid, uid):
        try:
            admins = self.graph_db.find_business_admins(bid)
        except DatabaseFindError as exc:
            logging.error('Could not execute cypher for business admins.')
            msg = {'message': 'Internal server error'}
            return msg, 500
        except DatabaseEmptyResult as exc:
            logging.debug('No admins were found for bid: {}'.format(bid))
            return None, 204

        return filter_user_info(admins), 200


class BusinessAdmin(Resource):
    def __init__(self):
        super(BusinessAdmin, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    def delete(self, uid, bid, admin_uid):
        try:
            existing_user = self.graph_db.find_single_user('uid', admin_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The uid you tried to add as admin does not exist bid: {}  uid: {}'.format(bid, admin_uid)}
            logging.error(msg)
            return msg, 400
        except DatabaseFindError as exc:
            logging.error('Could add uid as admin for business, uid find error: bid:{} uid: {}'.format(bid, admin_uid))
            msg = {'message': 'Internal server error'}
            return msg, 500

        responsible = existing_user.get('responsible_for')
        if responsible:
            if responsible.find(bid) >= 0:
                responsible_array = responsible.split()
                responsible_array.remove(bid)
                existing_user['responsible_for'] = ' '.join(responsible_array)
                try:
                    existing_user = self.graph_db.update(existing_user)
                except DocumentNotUpdated as exc:
                    logging.error('Could not add business admin: bid: {}  uid: {}'.format(bid, admin_uid))
                    msg = {'message': 'Internal server error'}
                    return msg, 500

                return None, 200

        msg = {'message': 'The uid you tried to delete from admins was not actually and admin'}
        logging.error(msg)
        return msg, 400
