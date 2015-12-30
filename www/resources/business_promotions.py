import datetime

__author__ = 'Mepla'

import logging

from flask_restful import Resource
from flask import request

from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, create_promotion_schema
from www import oauth2, db_helper
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseSaveError, \
    DatabaseFindError
from www.resources.utilities.helpers import filter_general_document_db_record
from www.resources.utilities.helpers import uuid_with_prefix


class BusinessPromotions(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, uid=None):
        try:
            promotions = self.doc_db.find_doc('bid', bid, 'business_promotions', limit=100)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_promotions.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204

        return filter_general_document_db_record(promotions)

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, bid, uid=None):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, create_promotion_schema)
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

        data['bid'] = bid
        data['pid'] = uuid_with_prefix('pid')

        try:
            self.doc_db.save(data, 'business_promotions')
            return filter_general_document_db_record(data), 201
        except DatabaseSaveError as exc:
            msg = {'message': 'Your promotion could not be saved. This is an internal error.'}
            logging.error(msg)
            return msg, 500


class BusinessPromotion(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, pid, uid=None):
        try:
            doc = self.doc_db.find_doc('pid', pid, 'business_promotions', 1)
            return filter_general_document_db_record(doc)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error(msg)
            return msg, 500
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'Business Promotion could not be found.'}
            logging.error(msg)
            return msg, 404

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def delete(self, bid, pid, uid=None):
        result = self.doc_db.delete('business_promotions', {'pid': pid})

        if result > 0:
            return None, 204
        else:
            msg = {'message': 'There is no promotion with pid ({}).'.format(pid)}
            logging.error(msg)
            return msg, 404


class EligiblePromotions(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, bid, uid=None):
        try:
            now_date = datetime.date.today().strftime('%Y-%m-%d')
            conditions = {'life_span.start_date': {'$lt': now_date}, 'life_span.end_date': {'$gt': now_date}}
            promotions = self.doc_db.find_doc('bid', bid, 'business_promotions', conditions=conditions, limit=100)

        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.error('Error reading database for business_promotions.')
            return msg, 500
        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'There are no promotions for this business.'}
            logging.error(msg)
            return msg, 204

        eligible_promotions = []

        for promotion in promotions:
            try:
                self.check_eligibility(promotion, uid)
                eligible_promotions.append(promotion)
            except DatabaseFindError as exc:
                msg = {'message': 'Internal server error.'}
                logging.info(msg)
                logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
                continue
            except DatabaseRecordNotFound:
                msg = {'message': 'User does not exist or does not have any checkins.'}
                logging.debug(msg)
                continue
            except Exception as exc:
                pass

        if len(eligible_promotions) < 1:
            return None, 204
        else:
            return filter_general_document_db_record(eligible_promotions)

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def check_eligibility(self, promotion, uid):
        graph_db = DatabaseFactory().get_database_driver('graph')
        user = graph_db.find_single_user('uid', uid)

        if not user:
            msg = {'message': 'No user with uid: {}'.format(uid)}
            logging.critical(msg)
            raise DatabaseRecordNotFound(msg)

        try:
            conditions = promotion.get('conditions')

            # Gender check
            gender_condition = conditions.get('gender')
            if gender_condition:
                if gender_condition != user.get('gender'):
                    raise Exception('Gender condition not satisfied.')

            # Age check
            age_condition = conditions.get('age')
            birth_date = user.get('birth_date')
            if not birth_date:
                raise Exception('Birth date not specified.')

            user_age = get_age(birth_date)

            min_age = age_condition.get('from')
            if min_age:
                if user_age < min_age:
                    raise Exception('User age is lower than minimum.')

            max_age = age_condition.get('to')
            if max_age:
                if user_age > max_age:
                    raise Exception('User age is higher than maximum.')

            # Checkins check
            checkins_condition = conditions.get('checkins')
            if checkins_condition:
                checkin = graph_db.find_single_user_checkins(uid, promotion.get('bid'))

                min_checkins_condition = checkins_condition.get('min')
                if min_checkins_condition:
                    if checkin.get('count') < min_checkins_condition:
                        raise Exception('Minimum number of checkins not met.')

                max_checkins_condition = checkins_condition.get('min')
                if max_checkins_condition:
                    if checkin.get('count') > max_checkins_condition:
                        raise Exception('Maximum number of checkins exceeded.')

                days_since_last_condition = checkins_condition.get('days_since_last')
                if days_since_last_condition:
                    last_checkin_timestamp = checkin.get('timestamps').split()[0]
                    last_checkin_date = datetime.datetime.fromtimestamp(last_checkin_timestamp)
                    actual_days_since_last_checkin = (datetime.datetime.today() - last_checkin_date).days

                    if actual_days_since_last_checkin < days_since_last_condition:
                        raise Exception('Number of days since last checkin is not met.')

                # Follow check
                follow_condition = checkins_condition.get('must_follow')
                if follow_condition:
                    is_follower = self.doc_db.is_follower(uid, promotion.get('bid'))
                    if not is_follower:
                        raise Exception('User must be a follower.')

        except Exception as exc:
            msg = 'Something went wrong in promotion eligibility check: {}: {}'.format(exc, exc.message)
            logging.error(msg)
            raise exc


class PromotionApply(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, bid, pid, uid=None):
        result = BusinessPromotion().get(bid, pid, uid)
        if not isinstance(result, dict):
            return result

        try:
            EligiblePromotions().check_eligibility(result, uid)
        except DatabaseFindError as exc:
            msg = {'message': 'Internal server error.'}
            logging.info(msg)
            logging.debug('Error querying graph database: {} -> {}'.format(exc, exc.message))
            return msg, 500
        except DatabaseRecordNotFound:
            msg = {'message': 'You are not eligible for this promotion.'}
            logging.debug(msg)
            return msg, 400
        except Exception as exc:
            msg = {'message': 'You are not eligible for this promotion.'}
            logging.debug(msg)
            return msg, 400
        
        rcid = uuid_with_prefix('rcid')
        redeem_code_doc = {'rcid': rcid, 'pid': pid, 'bid': bid, 'uid': uid}

        try:
            self.doc_db.save(result, 'redeem_codes')
            return filter_general_document_db_record(redeem_code_doc), 201
        except DatabaseSaveError as exc:
            msg = {'message': 'Your redeem code could not be generated. This is an internal error.'}
            logging.error(msg)
            return msg, 500


def get_age(birth_date):
        days_of_age = (datetime.datetime.today() - datetime.datetime.strptime(birth_date, '%Y-%m-%d')).days
        user_age = float(float(days_of_age)/float(365))
        return int(user_age)
