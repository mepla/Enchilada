from www.resources.accounting.point_transfer_reasons import PTR, Transaction
from www.resources.databases.factories import DatabaseFactory

__author__ = 'Mepla'


class Accountant(object):
    def __init__(self):
        self._db = DatabaseFactory().get_database_driver('documents/accounting')

    def apply_ptrs(self, ptrs):
        transaction = Transaction(ptrs)
        audited_transaction = Audit(transaction).process()
        for ptr in audited_transaction.ptrs:
            ptr.process()


class Audit(object):
    def __init__(self, transaction):
        assert isinstance(transaction, Transaction), 'isinstance(incr_ptr, IncrementalPTR)'
        self._transaction = transaction

    def process(self):
        return self._transaction

