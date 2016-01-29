from www.resources.accounting.accountant import Accountant

__author__ = 'Mepla'

from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseFindError
from www import oauth2, db_helper


class BusinessBalance(Resource):
    def __init__(self):
        self._accountant = Accountant()

    @oauth2.check_access_token
    @db_helper.handle_aliases
    # /businesses/<string:bid>/balances/<string:uid>
    def get(self, uid, bid):
        try:
            result = self._accountant.get_balance(uid, bid)
            return result
        except DatabaseFindError as exc:
            return {'message': 'Internal server error'}, 500
