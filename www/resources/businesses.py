from flask_restful.reqparse import RequestParser
from www.resources.config import configs
from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseFindError, DatabaseRecordNotFound, \
    DocumentNotUpdated, DatabaseEmptyResult

__author__ = 'Mepla'

from flask_restful import Resource
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, business_update_schema, business_signup_schema, \
    business_category_add_single_schema, add_admin_for_business_schema
from flask import request
from www.resources.utilities.helpers import filter_general_document_db_record, filter_user_info, \
    convert_str_query_string_to_bool, country_iso_of_location, distance_of_two_locations

import logging
from www import oauth2, db_helper
from www.resources.utilities.helpers import uuid_with_prefix


class Businesses(Resource):
    def __init__(self):
        super(Businesses, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
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

        body['email'] = body['email'].lower()
        try:
            return self.graph_db.create_new_business(**body)
        except Exception as exc:
            msg = {'message': 'Internal server error'}
            logging.error(exc, msg)
            return msg


    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid=None):
        parser = RequestParser()
        parser.add_argument('near_me', type=bool, help='`return_count` argument must be a boolean.')
        parser.add_argument('lat', type=float, help='`lat` argument must be a float.')
        parser.add_argument('lon', type=float, help='`lon` argument must be a float.')
        parser.add_argument('name', type=str, help='`name` argument must be a string.')
        parser.add_argument('country', type=str, help='`country` argument must be a string.')
        parser.add_argument('city', type=str, help='`city` argument must be a string.')
        parser.add_argument('category', type=str, help='`category` argument must be a string.')
        parser.add_argument('category_id', type=str, help='`category` argument must be a string.')
        parser.add_argument('rating', type=float, help='`rating` argument must be a float.')

        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('sort_by', type=str, help='`sort_by` argument must be a string.')

        args = parser.parse_args()

        near_me = convert_str_query_string_to_bool(args.get('near_me'))
        lat = args.get('lat')
        lon = args.get('lon')
        name = args.get('name')
        country = args.get('country')
        city = args.get('city')
        category = args.get('category')
        category_id = args.get('category_id')
        rating = args.get('rating')

        if near_me and (not lon or not lat):
            msg = {'message': 'You can not request near_me without providing `lat` and `lon`'}
            logging.debug(msg)
            return msg, 400

        conditions = {}

        if name:
            conditions['name'] = {"$regex": ".*{}.*".format(name), "$options": 'i'}

        if country or city or near_me:
            conditions['address'] = {}

        if country:
            conditions['address']['country'] = country.upper()

        if city:
            conditions['address']['city'] = {"$regex": ".*{}.*".format(city), "$options": 'i'}

        if category:
            category = ' '.join([x.capitalize() for x in category.split()])
            conditions['category'] = {'name': category}

        if category_id:
            conditions['category'] = {'id': category_id}

        if rating:
            conditions['reviews'] = {'average_rating': {'$gt': rating}}

        if near_me:
            iso = country_iso_of_location(lat, lon)
            if iso:
                conditions['address']['country'] = iso

        if len(conditions) < 1:
            msg = {'message': 'You can not request to find a business without any query strings.'}
            logging.debug(msg)
            return msg, 400

        try:
            businesses = self.doc_db.find_doc(None, None, 'business', conditions=conditions, limit=30)
            if near_me:
                near_me_distance = configs.get('POLICIES').get('near_distance')
                businesses_copy = list(businesses)
                businesses = []
                for biz in businesses_copy:
                    biz_lat = biz.get('address').get('lat')
                    biz_lon = biz.get('address').get('long')
                    d = distance_of_two_locations(lat, lon, biz_lat, biz_lon)
                    if d < near_me_distance:
                        biz['distance'] = round(d, 2)
                        businesses.append(biz)

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

        return filter_general_document_db_record(businesses)


class BusinessProfile(Resource):
    def __init__(self):
        super(BusinessProfile, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, bid):
        logging.debug('Client requested for business profile.')
        try:
            # existing_business = self.graph_db.find_single_business('bid', bid)
            # for key in existing_business.keys():
            #     value = existing_business[key]
            #     if isinstance(value, (str, unicode)) and '{' in value:
            #         try:
            #             existing_business[key] = json.loads(value)
            #         except Exception as exc:
            #             pass
            existing_business = self.doc_db.find_doc('bid', bid, 'business')

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error'}
            logging.error(exc, msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Business does not exist with this bid.'}
            logging.debug(msg)
            return msg, 404

        return existing_business

    @oauth2.check_access_token
    @db_helper.handle_aliases
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
    @db_helper.handle_aliases
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

    @oauth2.check_access_token
    @db_helper.handle_aliases
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
    @db_helper.handle_aliases
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
    @db_helper.handle_aliases
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
    @db_helper.handle_aliases
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
