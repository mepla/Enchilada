from www.resources.accounting.money import BaseMoneyExchange
from www.resources.databases.database_drivers import DatabaseSaveError
from www.resources.databases.factories import DatabaseFactory
from www.resources.utilities.helpers import uuid_with_prefix, date_now_formatted

__author__ = 'Mepla'


class PTRProcessException(Exception):
    pass


class BasePTR(object):
    def __init__(self, money_exchange, initiator_id, debtor_id, creditor_id):
        assert isinstance(money_exchange, BaseMoneyExchange), 'isinstance(single_exchange, BaseMoneyExchange)'
        self._money_exchange = money_exchange
        assert isinstance(initiator_id, (str, unicode)), 'isinstance(initiator_id, (str, unicode))'
        self._initiator_id = initiator_id
        assert isinstance(debtor_id, (str, unicode)), 'isinstance(debtor_id, (str, unicode))'
        self._debtor_id = debtor_id
        assert isinstance(creditor_id, (str, unicode)), 'isinstance(creditor_id, (str, unicode))'
        self._creditor_id = creditor_id
        self._description = None
        self._creation_date = date_now_formatted()
        self._settlement_date = None
        self._settled = False

    def process(self, transaction_id):
        pass

    def generate_log(self):
        log = {'initiator_id': self._initiator_id,
               'debtor_id': self._debtor_id,
               'creditor_id': self.creditor_id,
               'amount': self._money_exchange.amount,
               'currency': self._money_exchange.currency.currency_string,
               'creation_date': self._creation_date,
               'settled': self._settled,
               'settlement_date': self._settlement_date,
               'description': self._description,
               'data': {}}
        return log

    @property
    def money_exchange(self):
        return self._money_exchange

    @property
    def initiator_id(self):
        return self._initiator_id

    @initiator_id.setter
    def initiator_id(self, i):
        assert isinstance(i, (str, unicode)), 'isinstance(i, (str, unicode))'
        self._initiator_id = i

    @property
    def debtor_id(self):
        return self._debtor_id

    @debtor_id.setter
    def debtor_id(self, t):
        assert isinstance(t, (str, unicode)), 'isinstance(t, (str, unicode))'
        self._debtor_id = t

    @property
    def creditor_id(self):
        return self._creditor_id

    @creditor_id.setter
    def creditor_id(self, t):
        assert isinstance(t, (str, unicode)), 'isinstance(t, (str, unicode))'
        self._creditor_id = t

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, d):
        assert isinstance(d, str), 'isinstance(d, str)'
        self._description = d

    @property
    def creation_date(self):
        return self._creation_date

    @property
    def settled(self):
        return self._settled

    @property
    def settlement_date(self):
        return self._settlement_date

    @settlement_date.setter
    def settlement_date(self, d):
        self._settlement_date = d


class PTR(BasePTR):
    pass


class PromotionPTR(PTR):
    def __init__(self, money, initiator_id, debtor_id, creditor_id, pid):
        super(PromotionPTR, self).__init__(money, initiator_id, debtor_id, creditor_id)
        self._pid = pid

    def process(self, transaction_id):
        dbf = DatabaseFactory()
        acc_db = dbf.get_database_driver('docs/accounting')

        user_acc_doc = acc_db.find_doc('id', self._creditor_id, 'balances', 1)

        debtor_log = self.generate_log()
        debtor_log['creditor'] = 'echo'
        debtor_log['settled'] = False
        debtor_log['transaction_id'] = transaction_id

        try:
            acc_db.save(debtor_log, 'ptr_logs')
        except DatabaseSaveError as exc:
            raise PTRProcessException(exc.message)

        creditor_log = self.generate_log()
        creditor_log['debtor'] = 'echo'
        creditor_log['settled'] = True
        creditor_log['settlement_date'] = date_now_formatted()
        creditor_log['transaction_id'] = transaction_id

        if user_acc_doc['currency'] == self._money_exchange.currency.currency_string:
            amount_to_add = self._money_exchange.amount
        else:
            amount_to_add = self._money_exchange.currency.convert_to(user_acc_doc['currency'])
        user_acc_doc['balance'] += amount_to_add

        try:
            acc_db.save(user_acc_doc, 'balances')
            acc_db.save(creditor_log, 'ptr_logs')
        except DatabaseSaveError as exc:
            raise PTRProcessException(exc.message)

    def generate_log(self):
        log = super(PromotionPTR, self).generate_log()
        log['data'] = {'pid': self._pid}
        return log


class PurchasePTR(PTR):
    def __init__(self, money, multiplier, initiator_id, debtor_id, bid):
        super(PurchasePTR, self).__init__(money, multiplier, initiator_id, debtor_id)
        self._bid = bid


class TransferPTR(PTR):
    pass


class BaseTransaction(object):
    def __init__(self, ptrs):
        assert isinstance(ptrs, list), 'isinstance(ptrs, list)'
        self._ptrs = ptrs
        self._transaction_id = uuid_with_prefix('transaction')

    def add_ptr(self, ptr):
        assert isinstance(ptr, PTR), isinstance(ptr, PTR)
        self._ptrs.append(ptr)

    def remove_ptr(self, index):
        assert index < len(self._ptrs), 'index < len(self._ptrs)'
        del(self._ptrs[index])

    @property
    def ptrs(self):
        return self._ptrs

    @property
    def transaction_id(self):
        return self._transaction_id


class Transaction(BaseTransaction):
    pass
