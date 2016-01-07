from flask import request
from www.resources.json_schemas import validate_json, user_follow_req_accept_schema, JsonValidationException

__author__ = 'Mepla'

import logging

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.databases.factories import DatabaseFactory
from www import oauth2, db_helper


class UserFollowers(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, target_uid, uid=None):
        print('PATH: {} target_id: {}  uid: {}'.format(request.path, target_uid, uid))
        try:
            existing_user = self.graph_db.find_single_user('uid', target_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The user you tried to get followers of does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            response = self.graph_db.find_user_followers(target_uid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followers for this user.'}
            logging.debug(msg)
            return msg, 204

        return response


class UserFollowRequests(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, target_uid, uid=None):
        print('PATH: {} target_id: {}  uid: {}'.format(request.path, target_uid, uid))
        try:
            existing_user = self.graph_db.find_single_user('uid', target_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The user you tried to get followers of does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        try:
            response = self.graph_db.find_user_followers(target_uid, request=True)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followers for this user.'}
            logging.debug(msg)
            return msg, 204

        return response

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, target_uid, uid):
        try:
            if self.graph_db.is_follower(uid, target_uid):
                msg = {'message': 'You already follow this user.'}
                logging.debug(msg)
                return msg, 400
        except DatabaseRecordNotFound:
            msg = {'message': 'The user you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 404

        try:
            relation = self.graph_db.follow(uid, target_uid, request=True)
        except DatabaseRecordNotFound:
            msg = {'message': 'The user you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 400

        return relation


class UserFollowRequestAccept(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, target_uid, uid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, user_follow_req_accept_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        accept = data.get('accept') is True
        frid = data.get('frid')

        try:
            self.graph_db.accept_or_deny_follow_request(frid, accept)
        except DatabaseRecordNotFound:
            msg = {'message': 'Could not accept or deny follow request.'}
            logging.debug(msg)
            return msg, 400

        except Exception as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500
