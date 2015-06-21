__author__ = 'Mepla'

import logging
from uuid import uuid4
from py2neo import Graph, Node, Relationship, authenticate
from pymongo import MongoClient


class DatabaseFindError(Exception):
    pass

class DatabaseSaveError(Exception):
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

    def find_user(self, email):
        try:
            existing_user = self._graph.find_one('user', 'email', email)
        except Exception as exc:
            raise DatabaseFindError()

        if existing_user:
            return existing_user

        return None

    def users_with_udid(self, udid):
        existing_users_with_udid = self._graph.find('user', 'udid', udid, 4)
        count = 0
        for user in existing_users_with_udid:
            count += 1
        return count

    def create_new_business(self, **kwargs):
        kwargs['id'] = uuid4().hex
        new_business = Node('business', **kwargs)
        return self._graph.create(new_business)[0].properties

    def find_business(self, business_id):
        existing_business = self._graph.find_one('business', 'uid', business_id)
        if existing_business:
            return existing_business.properties

        return "Nothing is here for you!"