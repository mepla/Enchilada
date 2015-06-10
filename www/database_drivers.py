__author__ = 'Mepla'

from uuid import uuid4
from py2neo import Graph, Node, Relationship, authenticate


class GraphDatabaseBase(object):
    pass


class Neo4jDatabase(GraphDatabaseBase):
    def __init__(self, host='localhost', port=7474, username='neo4', password='new4j'):
        neo4j_address = host + ':' + str(port)
        authenticate(neo4j_address, username, password)
        self._graph = Graph('http://' + neo4j_address + '/db/data')

    def create_new_user(self, **kwargs):
        kwargs['id'] = uuid4().hex
        new_user = Node('user', **kwargs)
        return self._graph.create(new_user)[0].properties

    def find_user(self, **kwargs):
        if 'id' in kwargs:
            user_id = kwargs.get('id')
        elif 'email' in kwargs:
            email = kwargs.get('email')

    def user_exist(self, email):
        existing_user = self._graph.find_one('user', 'email', email)
        if existing_user:
            return True

        return False

    def users_with_udid(self, udid):
        existing_users_with_udid = self._graph.find('user', 'udid', udid, 4)
        count = 0
        for user in existing_users_with_udid:
            count += 1
        return count
