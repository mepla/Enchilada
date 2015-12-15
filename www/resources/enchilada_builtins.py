__author__ = 'Mepla'

import time


class BaseEntity(object):
    def __init__(self, entity_id):
        self.id = entity_id


class User(BaseEntity):
    def __init__(self, user_id, f_name, l_name, gender, email, creation_date=None, is_active=False, **kwargs):
        super(User, self).__init__(user_id)
        self.first_name = f_name
        self.last_name = l_name
        self.gender = gender
        self.email = email
        self.is_active = is_active
        self.creation_date = creation_date
        self.is_verified = kwargs.get('is_verified')
        self.password = kwargs.get('password')
        self.phones = kwargs.get('phones')
        self.cell_phones = kwargs.get('cell_phones')
        self.birth_date = kwargs.get('birth_date')
        self.country = kwargs.get('country')
        self.province = kwargs.get('province')
        self.city = kwargs.get('city')
        self.zip_code = kwargs.get('zip_code')
        self.image_link = kwargs.get('image_link')
        self.type = kwargs.get('type')


class Business(BaseEntity):
    def __init__(self, business_id, name, category, email, creation_date=None, is_active=False, **kwargs):
        super(Business, self).__init__(business_id)
        self.name = name
        self.category = category
        self.email = email
        self.is_active = is_active
        self.creation_date = creation_date
        self.description = kwargs.get('description')
        self.owner_name = kwargs.get('owner_name')
        self.owner_birth_date = kwargs.get('owner_birth_date')
        self.web_links = kwargs.get('web_links')
        self.title = kwargs.get('title')
        self.is_verified = kwargs.get('is_verified')
        self.password = kwargs.get('password')
        self.phones = kwargs.get('phones')
        self.cell_phones = kwargs.get('cell_phones')
        self.country = kwargs.get('country')
        self.province = kwargs.get('province')
        self.city = kwargs.get('city')
        self.zip_code = kwargs.get('zip_code')
        self.latitude = kwargs.get('latitude')
        self.longitude = kwargs.get('longitude')
        self.address = kwargs.get('address')
        self.image_links = kwargs.get('image_links')
        self.logo_link = kwargs.get('logo_link')
        self.hours = kwargs.get('hours')
        self.wifi = kwargs.get('wifi')
        self.reservations = kwargs.get('reservation')
        self.bank_info = kwargs.get('bank_info')

class CheckedIn(BaseEntity):
    def __init__(self, checkin_id, user_id, business_id, **kwargs):
        super(CheckedIn, self).__init__(checkin_id)
        self.user_id = user_id
        self.business_id = business_id
        self.count = kwargs.get('count')
        self.timestamps = kwargs.get('timestamps')
        self.referrer = kwargs.get('referrer')
        self.tokens = kwargs.get('tokens')
        self.loyalty = kwargs.get('loyalty')
        self.survey_result = kwargs.get('survey_result')

class Follow(BaseEntity):
    def __init__(self, follow_id, creation_date=None, type=None, status=0):
        super(Follow, self).__init__(follow_id)
        self.creation_date = creation_date
        self.status = status
        self.type = type


class IsChild(BaseEntity):
    def __init__(self, follow_id, creation_date=None, type=None, status=0):
        super(IsChild, self).__init__(follow_id)
        self.creation_date = creation_date
        self.status = status
        self.type = type

class BusinessCategory(BaseEntity):
    def __init__(self, category_id, name=None, parent_id=None, status=0):
        super(BusinessCategory, self).__init__(category_id)
        self.name = name
        self.parent = parent_id
        self.status = status

class Country(BaseEntity):
    def __init__(self, category_id, name, country_code):
        super(Country, self).__init__(category_id)
        self.name = name
        self.country_code = country_code

class Province(BaseEntity):
    def __init__(self, category_id, name, parent_country):
        super(Province, self).__init__(category_id)
        self.name = name
        self.parent_country = parent_country

class City(BaseEntity):
    def __init__(self, category_id, name, parent_country, parent_province):
        super(City, self).__init__(category_id)
        self.name = name
        self.parent_country = parent_country
        self.parent_province = parent_province
