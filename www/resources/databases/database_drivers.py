import pymongo

__author__ = 'Mepla'

import logging
import time
from operator import itemgetter

from py2neo import Graph, Node, Relationship, authenticate
from pymongo import MongoClient

from www.resources.utilities.helpers import uuid_with_prefix, utc_now_timestamp
from www.resources.utilities.helpers import filter_general_document_db_record, filter_user_info


class DatabaseFindError(Exception):
    pass


class DatabaseSaveError(Exception):
    pass


class DatabaseRecordNotFound(Exception):
    pass


class DocumentNotUpdated(Exception):
    pass


class DatabaseNotFound(Exception):
    pass


class DatabaseEmptyResult(Exception):
    pass


class GraphDatabaseBase(object):
    pass


class DocumentDatabaseBase(object):
    pass


class MongoDatabase(DocumentDatabaseBase):
    def __init__(self, host='localhost', port=27017, db='docs'):
        from www.resources.config import configs
        if configs['debug_mode']:
            docs = 'test_docs'
            auth = 'test_auth'
            accounting = 'test_accounting'
        else:
            docs = 'docs'
            auth = 'auth'
            accounting = 'accounting'

        self._mongo_client = MongoClient(host, port)

        if db == 'docs':
            self._mongo_db = self._mongo_client.test_docs
        elif db == 'auth':
            self._mongo_db = self._mongo_client.test_auth
        elif db == 'accounting':
            self._mongo_db = self._mongo_client.test_accounting
        else:
            raise DatabaseNotFound('The database you requested was not found: {}'.format(db))

        #self._mongo_client.admin.authenticate('default_access', 'Echomybiz')

    def save(self, doc, doc_type, multiple=False):
        if not doc_type:
            raise DatabaseSaveError('No doc_type provided.')

        try:
            if multiple:
                objs = self._mongo_db[doc_type].insert_many(doc, ordered=False)
            else:
                obj = self._mongo_db[doc_type].insert_one(doc)
        except Exception as exc:
            logging.error('Error saving doc to database: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseSaveError()

    def update(self, key, value, doc_type, updated_fields, conditions=None, multiple=False):
        if not doc_type:
            raise DatabaseSaveError('No doc_type provided.')

        try:
            find_predicate = {}
            if conditions:
                find_predicate = conditions

            if key and value:
                find_predicate[key] = value

            find_predicate = self._convert_conditions_to_mongo_style(find_predicate)

            if multiple:
                objs = self._mongo_db[doc_type].update_many(find_predicate, updated_fields)
            else:
                obj = self._mongo_db[doc_type].update_one(find_predicate, updated_fields)
        except Exception as exc:
            logging.error('Error updating doc: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseSaveError()

    def replace_a_doc(self, key, value, doc_type, doc, conditions=None):
        if not doc_type:
            raise DatabaseSaveError('No doc_type provided.')

        try:
            find_predicate = {}
            if conditions:
                find_predicate = conditions

            if key and value:
                find_predicate[key] = value

            find_predicate = self._convert_conditions_to_mongo_style(find_predicate)

            obj = self._mongo_db[doc_type].replace_one(find_predicate, doc)
        except Exception as exc:
            logging.error('Error updating doc: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseSaveError()

    def delete(self, doc_type, conditions, multiple=False):
        if multiple:
            result = self._mongo_db[doc_type].delete_many(conditions)
        else:
            result = self._mongo_db[doc_type].delete_one(conditions)

        return result.deleted_count

    def find_count(self, key, value, doc_type, conditions=None):
        try:
            find_predicate = {}
            if conditions:
                find_predicate = conditions

            if key and value:
                find_predicate[key] = value

            find_predicate = self._convert_conditions_to_mongo_style(find_predicate)

            count = self._mongo_db[doc_type].count(find_predicate)
            return count

        except DatabaseRecordNotFound as exc:
            raise exc

        except DatabaseEmptyResult as exc:
            raise exc

        except Exception as exc:
            logging.error('Error in finding doc in database: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseFindError()

    def find_doc(self, key, value, doc_type, limit=1, conditions=None, sort_key=None, sort_direction=1, force_array_return=False):
        print key, value, doc_type, conditions
        try:
            find_predicate = {}
            if conditions:
                find_predicate = conditions

            if key and value:
                find_predicate[key] = value

            find_predicate = self._convert_conditions_to_mongo_style(find_predicate)
            print(find_predicate)
            if limit == 1:
                doc = self._mongo_db[doc_type].find_one(find_predicate)
                if not doc:
                    raise DatabaseRecordNotFound()
                return_value = filter_general_document_db_record(doc, doc_type=doc_type)
                if force_array_return is True:
                    return [return_value]
                else:
                    return return_value
            else:
                if sort_key:
                    directon = pymongo.DESCENDING if sort_direction == -1 else pymongo.ASCENDING
                    cursor = self._mongo_db[doc_type].find(find_predicate, limit=limit).sort(sort_key, directon)
                else:
                    cursor = self._mongo_db[doc_type].find(find_predicate, limit=limit)
                return_list = []
                for doc in cursor:
                    return_list.append(filter_general_document_db_record(doc, doc_type=doc_type))
                if len(return_list) < 1:
                    raise DatabaseEmptyResult()
                return return_list

        except DatabaseRecordNotFound as exc:
            raise exc

        except DatabaseEmptyResult as exc:
            raise exc

        except Exception as exc:
            logging.error('Error in finding doc in database: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseFindError()

    def _convert_conditions_to_mongo_style(self, conditions):
        # TODO: This works a bit weird if the sub dictionary contains a dictionary that has a key starting with $ and other keys.
        return_conditions = {}
        for key, value in conditions.items():
            if isinstance(value, dict):
                child_dict = self._convert_conditions_to_mongo_style(value)
                for child_key, child_value in child_dict.items():
                    if child_key.startswith('$'):
                        return_conditions[key] = value
                    else:
                        root_key_str = str(key) + '.' + str(child_key)
                        return_conditions[root_key_str] = child_value
            else:
                return_conditions[key] = value
        return return_conditions


class Neo4jDatabase(GraphDatabaseBase):
    def __init__(self, host='localhost', port=7474, username='neo4', password='new4j'):
        neo4j_address = host + ':' + str(port)
        authenticate(neo4j_address, username, password)
        self._graph = Graph('http://' + neo4j_address + '/db/data')
        self.docs_in_memory = {}

    def find_all_nodes_with_label(self, label):
        results = self._graph.cypher.execute('match (n:{}) return n'.format(label))
        response = []
        for node in results:
            user_data = node.n.properties
            if 'type' in user_data:
                user_data['user_type'] = user_data['type']
                del user_data['type']
            response.append(filter_general_document_db_record(dict(user_data)))
        return response

    def update(self, doc):
        existing_doc = self.docs_in_memory.get(doc.get('uid')) or self.docs_in_memory.get(doc.get('bid')) or self.docs_in_memory.get(doc.get('rid')) or self.docs_in_memory.get(doc.get('id'))
        if existing_doc:
            try:
                for key in doc.keys():
                    existing_doc[key] = doc[key]
                existing_doc.push()
                return existing_doc.properties
            except Exception as exc:
                DocumentNotUpdated()
        else:
            raise DocumentNotUpdated()

    def create_new_user(self, **kwargs):
        new_user = Node('user', **kwargs)
        return self._graph.create(new_user)[0].properties

    def find_single_user(self, key, value):
        try:
            existing_user = self._graph.find_one('user', key, value)
        except Exception as exc:
            print(exc)
            raise DatabaseFindError()

        if existing_user:
            self.docs_in_memory[existing_user.properties.get('uid')] = existing_user
            return dict(existing_user.properties)
        else:
            raise DatabaseRecordNotFound()

    def find_single_user_checkins(self, user_id, bid=None):
        existing_user = self._graph.find_one('user', 'uid', user_id)
        if not existing_user:
            raise DatabaseRecordNotFound()

        existing_business = None
        if bid:
            existing_business = self._graph.find_one('business', 'bid', bid)
            if not existing_business:
                raise DatabaseRecordNotFound()

        try:
            checkin_relations = list(self._graph.match(start_node=existing_user, end_node=existing_business, rel_type="CHECK_IN"))
        except Exception as exc:
            raise DatabaseRecordNotFound()
        if checkin_relations:
            checkin_properties = []
            for checkin in checkin_relations:
                business = checkin.end_node
                resp = dict(checkin.properties)
                resp['business_bid'] = business.properties['bid']
                resp['business_name'] = business.properties['name']
                checkin_properties.append(resp)
            return checkin_properties
        else:
            raise DatabaseRecordNotFound()

    def users_with_udid_count(self, udid):
        existing_users_with_udid = self._graph.find('user', 'udid', udid, 4)
        count = 0
        for user in existing_users_with_udid:
            count += 1
        return count

    def create_new_business(self, **kwargs):
        kwargs['bid'] = uuid_with_prefix('bid')
        new_business = Node('business', **kwargs)
        return self._graph.create(new_business)[0].properties

    def find_single_business(self, key, value):
        try:
            existing_business = self._graph.find_one('business', key, value)
        except Exception as exc:
            raise DatabaseFindError()

        if existing_business:
            self.docs_in_memory[existing_business.properties.get('bid')] = existing_business
            return existing_business.properties
        else:
            raise DatabaseRecordNotFound

    def checkins_for_business(self, bid):
        try:
            business = self._graph.find_one('business', 'bid', bid)
            if not business:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        try:
            results = self._graph.match(None, "CHECK_IN", business)
            if not results:
                raise Exception()
        except Exception as exc:
            raise DatabaseEmptyResult

        print utc_now_timestamp()
        response_list = list()
        for res in results:
            user = res.start_node
            timestamps = res.properties['timestamps'].split(' ')
            for t in timestamps:
                response_list.append({'timestamp': t, 'uid': user.properties['uid'],
                                      'name': user.properties['f_name'] + ' ' + user.properties['l_name']})
        print utc_now_timestamp()

        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return response_list

    def accept_or_deny_follow_request(self, frid, accept=True, return_path_data=False):
        try:
            cypher_stat = "match ()-[r:FOLLOW_REQ {frid: '%s'}] -> () return r limit 1" % frid
            result = self._graph.cypher.execute(cypher_stat)
            friend_req = result.one
            if not friend_req:
                raise Exception
        except Exception as exc:
            raise DatabaseRecordNotFound()

        follower = friend_req.start_node
        followed = friend_req.end_node

        if accept is True:
            timestamp = str(utc_now_timestamp())
            new_id = uuid_with_prefix('fid')
            new_relation = Relationship(follower, "FOLLOWS", followed, fid=new_id, timestamp=timestamp)
            self._graph.create(new_relation)
            if return_path_data is True:
                return filter_user_info(new_relation.start_node.properties), new_relation.properties, \
                       filter_user_info(new_relation.end_node.properties)

        self._graph.delete(friend_req)

    def follow(self, uid, business_or_user_id, request=False, return_path_data=False):
        try:
            if business_or_user_id.find('uid') == 0:
                end_node = self._graph.find_one('user', 'uid', business_or_user_id)
            else:
                end_node = self._graph.find_one('business', 'bid', business_or_user_id)
            if not end_node:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        user = self._graph.find_one('user', 'uid', uid)

        rel_type = "FOLLOW_REQ" if request else "FOLLOWS"

        existing_relation = self._graph.match_one(user, rel_type, end_node)
        if existing_relation:
            return existing_relation.properties
        else:
            timestamp = str(utc_now_timestamp())
            if request is True:
                new_id = uuid_with_prefix('frid')
                new_relation = Relationship(user, rel_type, end_node, frid=new_id, timestamp=timestamp)
            else:
                new_id = uuid_with_prefix('fid')
                new_relation = Relationship(user, rel_type, end_node, fid=new_id, timestamp=timestamp)

            self._graph.create(new_relation)
            if return_path_data:
                return filter_user_info(user.properties), new_relation.properties, filter_user_info(end_node.properties)
            else:
                return new_relation.properties

    def find_business_followers(self, bid):
        try:
            business = self._graph.find_one('business', 'bid', bid)
            if not business:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        try:
            results = self._graph.match(None, "FOLLOWS", business)
            if not results:
                raise Exception()
        except Exception as exc:
            raise DatabaseEmptyResult

        response_list = list()
        for res in results:
            user = res.start_node
            timestamp = res.properties['timestamp']
            response_list.append({'timestamp': timestamp, 'user': filter_user_info(user.properties)})

        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return response_list

    def find_user_followers(self, uid, request=False):
        try:
            user = self._graph.find_one('user', 'uid', uid)
            if not user:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        try:
            rel_type = "FOLLOW_REQ" if request else "FOLLOWS"
            results = self._graph.match(None, rel_type, user)
            if not results:
                raise Exception()
        except Exception as exc:
            raise DatabaseEmptyResult

        response_list = list()
        id_prefix = "frid" if request else "fid"
        for res in results:
            user = res.start_node
            timestamp = res.properties['timestamp']
            response_list.append({'timestamp': timestamp, 'user': filter_user_info(user.properties), id_prefix: res.properties.get(id_prefix)})

        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return response_list

    def find_user_followings(self, uid, users=True, businesses=True):
        try:
            user = self._graph.find_one('user', 'uid', uid)
            if not user:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        following_type = ''
        if not businesses and not users:
            raise DatabaseEmptyResult()
        if users and not businesses:
            following_type = ':user'
        if businesses and not users:
            following_type = ":business"

        try:
            cypher_statement = "match (n:user {uid: '%s'}) -[r:FOLLOWS]-> (m%s) return r" % (uid, following_type)
            results = self._graph.cypher.execute(cypher_statement)
            if not results:
                raise Exception()
        except Exception as exc:
            raise DatabaseEmptyResult()

        response_list = list()
        for record in results:
            res = record.r
            end_node = res.end_node
            timestamp = res.properties['timestamp']
            response_list.append({'timestamp': timestamp, 'following': end_node.properties})

        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return response_list

    def is_follower(self, uid, business_or_user_id):
        try:
            if business_or_user_id.find('uid') == 0:
                end_node = self._graph.find_one('user', 'uid', business_or_user_id)
            else:
                end_node = self._graph.find_one('business', 'bid', business_or_user_id)
            if not end_node:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        user = self._graph.find_one('user', 'uid', uid)

        existing_relation = self._graph.match_one(user, "FOLLOWS", end_node)
        if existing_relation:
            return True
        else:
            return False

    def checkin_user(self, business_id, user_id):
        try:
            business = self._graph.find_one('business', 'bid', business_id)
            if not business:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        user = self._graph.find_one('user', 'uid', user_id)

        existing_relation = self._graph.match_one(user, "CHECK_IN", business)
        if existing_relation:
            existing_relation.properties['count'] += 1
            existing_relation.properties['last_checkin'] = utc_now_timestamp()
            existing_relation.push()
            return existing_relation.properties
        else:
            new_id = uuid_with_prefix('rid')
            first_checkin_date = utc_now_timestamp()
            last_checkin_date = first_checkin_date
            new_relation = Relationship(user, 'CHECK_IN', business, rid=new_id, count=1, first_checkin=first_checkin_date, last_checkin=last_checkin_date)
            self._graph.create(new_relation)
            return new_relation.properties

    def find_business_admins(self, bid):
        try:
            result = self._graph.cypher.execute('match (n:user) where n.responsible_for =~ \'^.*{}.*$\' return n'.format(bid))
        except Exception as exc:
            logging.error(exc)
            raise DatabaseFindError

        if len(result.records) < 1:
            raise DatabaseEmptyResult

        else:
            return [admin.n.properties for admin in result.records]

    def find_all_checkins_of_a_list(self, list_of_uids):
        try:
            result = self._graph.cypher.execute('match (n:user) -[r:]- where n.uid in {} return n order by n.email DESC limit 2'.format(list_of_uids))
        except Exception as exc:
            logging.error(exc)
            raise DatabaseFindError

        if len(result.records) < 1:
            raise DatabaseEmptyResult

        else:
            return [admin.n.properties for admin in result.records]
