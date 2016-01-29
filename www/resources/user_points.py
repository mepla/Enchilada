import logging
from flask_restful.reqparse import RequestParser
from www.resources.config import configs

__author__ = 'Mepla'


from www.resources.accounting.accountant import Accountant
from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseFindError
from www import oauth2, db_helper


class UserPointTransactions(Resource):
    def __init__(self):
        self._accountant = Accountant()

    @oauth2.check_access_token
    @db_helper.handle_aliases
    # /users/<string:target_uid>/point_transactions
    def get(self, uid, target_uid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('user_role', type=str, help='`user_role` argument must be one of these: `all`, `creditor` or `debtor`')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')

        if before and after and before < after:
            msg = {'message': '`before` argument must be greater than or equal to `after`.'}
            logging.debug(msg)
            return msg, 400

        limit = args.get('limit')
        max_limit = configs.get('DATABASES').get('mongodb').get('max_page_limit')
        if not limit or limit > max_limit:
            limit = max_limit

        user_role = args.get('user_role')

        try:
            result = self._accountant.get_point_transactions(target_uid, limit=limit, before=before, after=after, user_role=user_role)
            return result
        except DatabaseFindError as exc:
            return {'message': 'Internal server error'}, 500
