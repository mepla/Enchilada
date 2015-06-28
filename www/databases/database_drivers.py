__author__ = 'Mepla'

import logging
from uuid import uuid4
from py2neo import Graph, Node, Relationship, authenticate, rel
from pymongo import MongoClient
import time

class DatabaseFindError(Exception):
    pass

class DatabaseSaveError(Exception):
    pass

class DatabaseRecordNotFound(Exception):
    pass

class DatabaseNotFound(Exception):
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

    def save(self, doc):
        if 'type' not in doc:
            raise DatabaseSaveError('Your document must include a \'type\'.')

        doc_type = doc['type']

        try:
            obj = self._mongo_db[doc_type].insert_one(doc)
        except Exception as exc:
            logging.error('Error saving doc to database: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseSaveError()

    def find_doc(self, key, value, doc_type, limit=1):
        try:
            if limit == 1:
                return self._mongo_db[doc_type].find_one({key: value})
            else:
                cursor = self._mongo_db[doc_type].find({key: value})
                return_list = []
                for doc in cursor:
                    return_list.append(doc)
                return return_list

        except Exception as exc:
            logging.error('Error in finding doc in database: {} exc: {}'.format(self._mongo_db, exc))
            raise DatabaseFindError()

class Neo4jDatabase(GraphDatabaseBase):
    def __init__(self, host='localhost', port=7474, username='neo4', password='new4j'):
        neo4j_address = host + ':' + str(port)
        authenticate(neo4j_address, username, password)
        self._graph = Graph('http://' + neo4j_address + '/db/data')

    def create_new_user(self, **kwargs):
        kwargs['id'] = uuid4().hex
        new_user = Node('user', **kwargs)
        return self._graph.create(new_user)[0].properties

    def find_single_user(self, key, value):
        try:
            existing_user = self._graph.find_one('user', key, value)
            checkin_relations = self._graph.match(start_node=existing_user, rel_type="CHECK_IN")
        except Exception as exc:
            raise DatabaseFindError()

        if existing_user:
            existing_user_copy = dict(existing_user.properties)
            if checkin_relations:
                checkins_list = list()
                for checkin in checkin_relations:
                    checkins_list.append(dict(checkin.properties))
                existing_user_copy["checkins"] = checkins_list
            return existing_user_copy
        else:
            raise DatabaseRecordNotFound

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

    def checkin_user(self, business_id, user_id):
        try:
            business = self._graph.find_one('business', 'bid', business_id)
            if not business:
                raise Exception()
        except Exception as exc:
            raise DatabaseRecordNotFound()

        user = self.find_single_user('uid', user_id)

        existing_relation = self._graph.match_one(user, "CHECK_IN", business)
        if existing_relation:
            existing_relation.properties['count'] += 1
            existing_relation.properties['timestamps'] = str(time.time()) + ' ' + existing_relation.properties['timestamps']
            existing_relation.push()
            return existing_relation.properties
        else:
            new_id = str(uuid4())
            timestamps = str(time.time())
            new_relation = Relationship(user, 'CHECK_IN', business, id=new_id, count=1, timestamps=timestamps)
            self._graph.create(new_relation)
            return new_relation.properties
