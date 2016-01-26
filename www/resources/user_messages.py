from www.resources.config import configs

__author__ = 'Mepla'

import time
import logging

from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import request

from www.resources.databases.database_drivers import DatabaseSaveError, DatabaseRecordNotFound, DatabaseFindError, \
    DatabaseEmptyResult
from www.resources.utilities.helpers import uuid_with_prefix, utc_now_timestamp, convert_str_query_string_to_bool, \
    filter_user_info
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException, message_post_schema, message_put_schema
from www.resources.utilities.helpers import filter_general_document_db_record
from www import oauth2, db_helper


class UserMessages(Resource):
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
        parser.add_argument('include_info', type=bool, help='`include_info` argument must be a boolean.')

        args = parser.parse_args()
        include_info = convert_str_query_string_to_bool(args.get('include_info'))

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
            conditions["$or"] = [{'sender': target_uid}, {'receiver': target_uid}]
            messages = self.doc_db.find_doc(None, None, 'user_messages', limit=limit, conditions=conditions, sort_key='timestamp', sort_direction=-1)

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

        if include_info:
            entities_info = {}
            for msg in messages:
                entity_id = None
                if msg.get('sender') == target_uid:
                    entity_id = msg.get('receiver')
                elif msg.get('receiver') == target_uid:
                    entity_id = msg.get('sender')

                if entity_id:
                    existing_entity = entities_info.get(entity_id)
                    if existing_entity:
                        msg['info'] = existing_entity
                    else:
                        entity_type = None
                        if entity_id.startswith('bid'):
                            entity_type = 'bid'
                        elif entity_id.startswith('uid'):
                            entity_type = 'uid'
                        if entity_type:
                            try:
                                entity_info = self.doc_db.find_doc(entity_type, entity_id, 'business' if entity_type == 'bid' else 'user')
                                msg['info'] = filter_user_info(entity_info)
                                entities_info[entity_id] = msg['info']
                            except Exception as exc:
                                logging.error('Could not load {} info ({}) in messages collection: {}'.format(entity_type, entity_id, exc))

        return filter_general_document_db_record(messages)

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
            validate_json(data, message_post_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            existing_user = self.graph_db.find_single_user('uid', target_uid)
        except DatabaseRecordNotFound as exc:
            msg = {'message': 'The user you tried to post message to does not exist.'}
            logging.debug(msg)
            return msg, 404

        except DatabaseFindError as exc:
            msg = {'message': 'Could not retrieve requested information'}
            logging.error(msg)
            return msg, 500

        doc = {'data': data, 'timestamp': utc_now_timestamp(), 'sender': uid, 'receiver': target_uid, 'mid': uuid_with_prefix('mid'), 'seen': False}

        try:
            self.doc_db.save(doc, 'user_messages')
        except DatabaseSaveError as exc:
            msg = {'message': 'Your changes may have been done partially or not at all.'}
            logging.error(msg)
            return msg, 500

        return None, 201


class UserMessage(Resource):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def get(self, uid, target_uid, mid):
        try:
            message = self.doc_db.find_doc('mid', mid, 'user_messages', 1)

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

        return filter_general_document_db_record(message)

    @oauth2.check_access_token
    @db_helper.handle_aliases
    def put(self, uid, target_uid, mid):
        try:
            data = request.get_json(force=True, silent=False)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.'}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(data, message_put_schema)
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.error(msg)
            return msg, 400

        is_seen = data.get('seen')

        try:
            message = self.doc_db.update('mid', mid, 'user_messages', {'$set': {'seen': is_seen}})
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

        return filter_general_document_db_record(message)
