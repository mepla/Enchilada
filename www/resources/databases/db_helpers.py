import logging
from functools32 import wraps
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseFindError
from www.resources.databases.factories import DatabaseFactory

__author__ = 'Mepla'


class DBHelper(object):
    def __init__(self):
        self.docs_db = DatabaseFactory().get_database_driver('document/docs')
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    def handle_aliases(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                for key, value in kwargs.items():
                    if 'hrbid' in value:
                        existing_biz = self.docs_db.find_doc('hrbid', value, 'business')
                        kwargs[key] = existing_biz.get('bid')

                    elif 'hruid' in value:
                        existing_user = self.docs_db.find_doc('hruid', value, 'user')
                        kwargs[key] = existing_user.get('uid')

                return f(*args, **dict(kwargs.items()))

            except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
                msg = {'message': 'The url you requested does not exist.'}
                logging.debug(msg)
                return msg, 404

            except DatabaseFindError as exc:
                msg = {'message': 'Internal server error.'}
                logging.info(msg)
                logging.debug('Error querying database: {} -> {}'.format(exc, exc.message))
                return msg, 500

            except Exception as exc:
                msg = {'message': 'Internal server error.'}
                logging.info(msg)
                logging.debug('General exception: {} -> {}'.format(exc, exc.message))
                return msg, 500

        return wrapper
