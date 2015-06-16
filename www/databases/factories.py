__author__ = 'Mepla'

import logging

from www.databases.database_drivers import Neo4jDatabase, MongoDatabase, DatabaseNotFound
from www.config import configs

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseFactory(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._databases = []

    def get_database_driver(self, db_type='document/docs'):

        logging.debug('A database driver is requested of type: {}'.format(db_type))
        if db_type == 'document/docs':
            mongo_db_configs = configs.get('DATABASES').get('mongodb')
            mongo_db_instance = MongoDatabase(mongo_db_configs.get('host'), mongo_db_configs.get('port'), 'docs')
            logging.debug('Database driver of type `{}` was created and returned: {}'.format(db_type, mongo_db_instance))
            return mongo_db_instance

        if db_type == 'document/auth':
            mongo_db_configs = configs.get('DATABASES').get('mongodb')
            mongo_db_instance = MongoDatabase(mongo_db_configs.get('host'), mongo_db_configs.get('port'), 'auth')
            logging.debug('Database driver of type `{}` was created and returned: {}'.format(db_type, mongo_db_instance))
            return mongo_db_instance

        elif db_type == 'graph':
            neo4j_configs = configs.get('DATABASES').get('neo4j')
            neo4j_instance = Neo4jDatabase(neo4j_configs.get('host'), neo4j_configs.get('port'),
                                           neo4j_configs.get('username'), neo4j_configs.get('password'))
            self._databases.append(neo4j_instance)
            logging.debug('Database driver of type `{}` was created and returned: {}'.format(db_type, neo4j_instance))
            return neo4j_instance
        else:
            raise DatabaseNotFound()
