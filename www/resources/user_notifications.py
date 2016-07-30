from www.resources.config import configs
from www.resources.json_schemas import validate_json, JsonValidationException, \
    user_notification_seen_schema

__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request

from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.utilities.helpers import uuid_with_prefix, utc_now_timestamp, convert_str_query_string_to_bool
from www.resources.databases.factories import DatabaseFactory
from www.resources.utilities.helpers import filter_general_document_db_record
from www import oauth2, db_helper


class UserNotifications(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, target_uid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('include_seen', type=str, help='`include_seen` argument must be a boolean.')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')
        include_seen = convert_str_query_string_to_bool(args.get('include_seen'))

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

        if include_seen is False:
            conditions['seen'] = False

        try:
            messages = self.doc_db.find_doc('uid', uid, 'user_notifications', limit=limit, conditions=conditions, sort_key='timestamp', sort_direction=-1)

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The information you requested is not found'}
            logging.info(msg)
            return msg, 404

        except DatabaseEmptyResult as exc:
            msg = {'message': 'There are no messages.'}
            logging.info(msg)
            return msg, 204

        return filter_general_document_db_record(messages)


class UserNotificationsSeen(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def post(self, uid, target_uid):
        try:
            self.doc_db.update('uid', target_uid, 'user_notifications', {'$set': {'seen': True}},
                               conditions={'seen': False}, multiple=True)
        except Exception as exc:
            msg = {'message': 'Could not mark notifications as read',
                   'error': 'internal_server_error'}
            logging.error('{}: {}'.format(msg.get('message'), exc))
            return msg, 500


class UserNotificationDelete(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def delete(self, uid, target_uid,notification_id):
        try:
            self.doc_db.delete('uid', target_uid, 'user_notifications', {'$set': {'seen': True}}, conditions={'seen': False}, multiple=True)
        except Exception as exc:
            msg = {'message': 'Could not mark notifications as read',
                   'error': 'internal_server_error'}
            logging.error('{}: {}'.format(msg.get('message'), exc))
            return msg, 500