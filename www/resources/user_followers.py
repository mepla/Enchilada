from flask import request

from www.resources.json_schemas import validate_json, user_follow_req_accept_schema, JsonValidationException
from www.resources.notifications.notification_manager import NotificationManager
from www.resources.utilities.helpers import filter_user_info

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
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

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
            neo_result = self.graph_db.find_user_followers(target_uid)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followers for this user.'}
            logging.debug(msg)
            return msg, 204

        if len(neo_result) == 0:
            return '', 204

        following_uids = [x.get('user').get('uid') for x in neo_result]
        conditions = {'uid': {'$in': following_uids}}
        mongo_result = self.doc_db.find_doc(None, None, 'user', 10000, conditions)
        for i in range(0, len(neo_result)):
            neo_result[i]['user'] = mongo_result[i]

        return neo_result


class UserFollowRequests(Resource):
    def __init__(self):
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.notification_manager = NotificationManager()

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
            neo_result = self.graph_db.find_user_followers(target_uid, request=True)
        except DatabaseEmptyResult:
            msg = {'message': 'There is no followers for this user.'}
            logging.debug(msg)
            return msg, 204

        following_uids = [x.get('user').get('uid') for x in neo_result]
        conditions = {'uid': {'$in': following_uids}}
        mongo_result = self.doc_db.find_doc(None, None, 'user', 10000, conditions)
        for i in range(0, len(neo_result)):
            neo_result[i]['user'] = mongo_result[i]

        return neo_result

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
            follower, relation, followee = self.graph_db.follow(uid, target_uid, request=True, return_path_data=True)
        except DatabaseRecordNotFound:
            msg = {'message': 'The user you tried to follow does not exist.'}
            logging.debug(msg)
            return msg, 400

        try:
            self.notification_manager.add_notification('follow_request', {'follower': uid, 'followee': target_uid,
                                                                          'frid': relation.get('frid'),
                                                                          'follower_data': follower})
        except:
            pass

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
            result = self.graph_db.accept_or_deny_follow_request(frid, accept)
            # if accept is True:
            #     follower, relation, followee = result

        except DatabaseRecordNotFound:
            msg = {'message': 'Could not accept or deny follow request.'}
            logging.debug(msg)
            return msg, 400

        except Exception as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500
