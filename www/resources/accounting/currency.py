from types import NoneType

__author__ = 'Mepla'


class BaseCurrency(object):
    def __init__(self, currency_string, currency_full_name=None, online=True, changeable=True):
        assert isinstance(currency_string, (str, unicode))
        self._currency_string = currency_string
        assert isinstance(currency_full_name, (str, unicode, NoneType))
        self._currency_full_name = currency_full_name
        assert isinstance(currency_full_name, (bool, NoneType))
        self._online = online
        assert isinstance(changeable, (bool, NoneType))
        self._changeable = changeable

    def convert_to(self, other_currency):
        pass

    @property
    def currency_string(self):
        return self._currency_string

    @property
    def currency_full_name(self):
        return self._currency_full_name

    @property
    def online(self):
        return self._online

    @property
    def changeable(self):
        return self._changeable


class EchoCurrency(BaseCurrency):
    def __init__(self, currency_string, currency_full_name):
        super(EchoCurrency, self).__init__(currency_string=currency_string, currency_full_name=currency_full_name, online=True, changeable=True)


class EchoGlobalCurrency(EchoCurrency):
    def __init__(self):
        super(EchoGlobalCurrency, self).__init__('EGP', 'Echo Global Point')


class BusinessSpecificCurrency(EchoCurrency):
    def __init__(self):
        super(BusinessSpecificCurrency, self).__init__('BSP', 'Business Specific Point')