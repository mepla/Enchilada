__author__ = 'Mepla'

from www.resources.accounting.currency import BaseCurrency, EchoGlobalCurrency, BusinessSpecificCurrency


class BaseMoneyExchange(object):
    def __init__(self, currency, amount):
        assert isinstance(currency, BaseCurrency), 'isinstance(currency, BaseCurrency)'
        self._currency = currency
        assert isinstance(amount, (int, float)), 'isinstance(amount, (int, float))'
        self._amount = amount

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, a):
        assert isinstance(a, (int, float)), 'isinstance(a, (int, float))'
        self._amount = a

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, c):
        assert isinstance(c, BaseCurrency), 'isinstance(c, BaseCurrency)'
        self._currency = c


class EchoGlobalPoint(BaseMoneyExchange):
    def __init__(self, amount):
        super(EchoGlobalPoint, self).__init__(EchoGlobalCurrency(), amount=amount)


class BusinessSpecificPoint(BaseMoneyExchange):
    def __init__(self, amount):
        super(BusinessSpecificPoint, self).__init__(BusinessSpecificCurrency(), amount=amount)
