import logging
from www.resources.accounting.point_transfer_reasons import PTR, Transaction
from www.resources.databases.database_drivers import DatabaseRecordNotFound, DatabaseEmptyResult, DatabaseFindError
from www.resources.databases.factories import DatabaseFactory
from www.resources.utilities.helpers import filter_general_document_db_record

__author__ = 'Mepla'


class Accountant(object):
    def __init__(self):
        self._db = DatabaseFactory().get_database_driver('document/accounting')

    def apply_ptrs(self, ptrs):
        transaction = Transaction(ptrs)
        audited_transaction = Audit(transaction).process()
        for ptr in audited_transaction.ptrs:
            ptr.process()

    def get_point_transactions(self, uid, bid, before=None, after=None, limit=None):
        try:
            conditions = {'$or': [{"creditor": bid, 'debtor': uid}, {"creditor": uid, 'debtor': bid}]}

            if before:
                conditions['timestamp'] = {'$lt': before}

            if after:
                if conditions.get('timestamp'):
                    conditions['timestamp']['$gt'] = after
                else:
                    conditions['timestamp'] = {'$gt': after}

            if limit and isinstance(limit, int):
                result_doc = self._db.find_doc(None, None, 'point_transactions', conditions=conditions, sort_key='timestamp', sort_direction=-1, limit=limit)
            else:
                result_doc = self._db.find_doc(None, None, 'point_transactions', conditions=conditions, sort_key='timestamp', sort_direction=-1)
            return filter_general_document_db_record(result_doc)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            return []

        except DatabaseFindError as exc:
            logging.error('Error finding document in point_transactions: {}'.format(exc))
            raise exc

    def get_balance(self, uid, bid):
        try:
            result_doc = self._db.find_doc("bid", bid, 'balances', limit=1, conditions={'uid': uid})
            return filter_general_document_db_record(result_doc)

        except (DatabaseRecordNotFound, DatabaseEmptyResult) as exc:
            return {'bid': bid, 'uid': uid, 'balance': 0, 'total_earned': 0, 'currency': ''}

        except DatabaseFindError as exc:
            logging.error('Error finding document in balances: {}'.format(exc))
            raise exc


class Audit(object):
    def __init__(self, transaction):
        assert isinstance(transaction, Transaction), 'isinstance(incr_ptr, IncrementalPTR)'
        self._transaction = transaction

    def process(self):
        return self._transaction

