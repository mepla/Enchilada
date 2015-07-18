__author__ = 'Mepla'

import logging
from uuid import uuid4
from py2neo import Graph, Node, Relationship, authenticate, rel
from pymongo import MongoClient
from www.resources.helpers import filter_general_document_db_record
import time
from operator import itemgetter


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
        from www.config import configs
        if configs['debug_mode']:
            docs = 'test_docs'
            auth = 'test_auth'
        else:
            docs = 'docs'
            auth = 'auth'

        self._mongo_client = MongoClient(host, port)
        if db == 'docs':
            self._mongo_db = self._mongo_client.test_docs
        elif db == 'auth':
            self._mongo_db = self._mongo_client.test_auth
        else:
            raise DatabaseNotFound('The database you requested was not found: {}'.format(db))

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

    def find_doc(self, key, value, doc_type, limit=1, conditions=None):
        try:
            find_predicate = {}
            if conditions:
                find_predicate = conditions

            if key and value:
                find_predicate[key] = value

            if limit == 1:
                doc = self._mongo_db[doc_type].find_one(find_predicate)
                if not doc:
                    raise DatabaseRecordNotFound
                return doc
            else:
                cursor = self._mongo_db[doc_type].find(find_predicate)
                return_list = []
                for doc in cursor:
                    return_list.append(filter_general_document_db_record(doc))
                if len(return_list) < 1:
                    raise DatabaseEmptyResult()
                return return_list

        except DatabaseRecordNotFound as exc:
            raise exc
        except Exception as exc:
            logging.error('Error in finding doc in database: {} exc: {}'.format(self._mongo_db,type(exc)))
            raise DatabaseFindError()


class Neo4jDatabase(GraphDatabaseBase):
    def __init__(self, host='localhost', port=7474, username='neo4', password='new4j'):
        neo4j_address = host + ':' + str(port)
        authenticate(neo4j_address, username, password)
        self._graph = Graph('http://' + neo4j_address + '/db/data')
        self.docs_in_memory = {}

    def update(self, doc):
        existing_doc = self.docs_in_memory[doc.get('uid')] or self.docs_in_memory[doc.get('bid')] or self.docs_in_memory[doc.get('rid')] or self.docs_in_memory[doc.get('id')]
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
            self.docs_in_memory[existing_user.properties.get('uid')] = existing_user
        except Exception as exc:
            raise DatabaseFindError()

        if existing_user:
            return dict(existing_user.properties)
        else:
            raise DatabaseRecordNotFound

    def find_single_user_checkins(self, user_id):
        existing_user = self._graph.find_one('user', 'uid', user_id)
        if not existing_user:
            raise DatabaseRecordNotFound()
        try:
            checkin_relations = list(self._graph.match(start_node=existing_user, rel_type="CHECK_IN"))
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
        kwargs['id'] = uuid4().hex
        new_business = Node('business', **kwargs)
        return self._graph.create(new_business)[0].properties

    def find_single_business(self, key, value):
        try:
            existing_business = self._graph.find_one('business', key, value)
        except Exception as exc:
            raise DatabaseFindError()

        if existing_business:
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

        print time.time()
        response_list = list()
        for res in results:
            user = res.start_node
            timestamps = res.properties['timestamps'].split(' ')
            for t in timestamps:
                response_list.append({'timestamp': t, 'uid': user.properties['uid'],
                                      'name': user.properties['f_name'] + ' ' + user.properties['l_name']})
        print time.time()

        response_list = sorted(response_list, key=itemgetter('timestamp'), reverse=True)
        return response_list

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
            existing_relation.properties['timestamps'] = str(time.time()) + ' ' + existing_relation.properties['timestamps']
            existing_relation.push()
            return existing_relation.properties
        else:
            new_id = str(uuid4())
            timestamps = str(time.time())
            new_relation = Relationship(user, 'CHECK_IN', business, rid=new_id, count=1, timestamps=timestamps)
            self._graph.create(new_relation)
            return new_relation.properties
