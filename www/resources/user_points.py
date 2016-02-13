import logging
from flask_restful.reqparse import RequestParser
from www.resources.config import configs
from www.resources.databases.factories import DatabaseFactory
from www.resources.utilities.helpers import convert_str_query_string_to_bool

__author__ = 'Mepla'


from www.resources.accounting.accountant import Accountant
from flask_restful import Resource

from www.resources.databases.database_drivers import DatabaseFindError
from www import oauth2, db_helper


class UserPointTransactions(Resource):
    def __init__(self):
        self._accountant = Accountant()
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')

    @oauth2.check_access_token
    @db_helper.handle_aliases
    # /users/<string:target_uid>/point_transactions
    def get(self, uid, target_uid):
        parser = RequestParser()
        parser.add_argument('limit', type=int, help='`limit` argument must be an integer.')
        parser.add_argument('before', type=float, help='`before` argument must be a timestamp (float).')
        parser.add_argument('after', type=float, help='`after` argument must be a timestamp (float).')
        parser.add_argument('user_role', type=str, help='`user_role` argument must be one of these: `all`, `creditor` or `debtor`')
        parser.add_argument('include_business_info', type=bool, help='`include_business_info` argument must be a boolean.')

        args = parser.parse_args()

        before = args.get('before')
        after = args.get('after')
        include_business_info = convert_str_query_string_to_bool(args.get('include_business_info'))

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
            if include_business_info:
                business_infos = {}
                for transaction in result:
                    creditor = transaction.get('creditor')
                    debtor = transaction.get('debtor')
                    if creditor == target_uid:
                        transaction_bid = debtor
                    else:
                        transaction_bid = creditor

                    try:
                        existing_biz = business_infos.get(transaction_bid)
                        if not existing_biz:
                            existing_biz = self.doc_db.find_doc('bid', transaction_bid, doc_type='business', limit=1)
                            business_infos[transaction_bid] = self.filter_business_info_for_transactions(existing_biz)
                        transaction['business'] = business_infos.get(transaction_bid)
                    except Exception as exc:
                        logging.error('Could not fetch user info in User checkins: {}'.format(exc))

            return result
        except DatabaseFindError as exc:
            return {'message': 'Internal server error'}, 500

    def filter_business_info_for_transactions(self, business_info):
        filtered_info = {}
        if 'name' in business_info:
            filtered_info['name'] = business_info['name']
        if 'address' in business_info:
            filtered_info['address'] = business_info['address']
        if 'hrbid' in business_info:
            filtered_info['hrbid'] = business_info['hrbid']
        if 'gallery' in business_info:
            filtered_info['gallery'] = business_info['gallery']
        if 'metrics' in business_info:
            filtered_info['metrics'] = business_info['metrics']

        return filtered_info