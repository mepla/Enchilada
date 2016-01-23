import collections
import logging
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException
from www.resources.utilities.helpers import utc_now_timestamp, uuid_with_prefix
import smtplib


__author__ = 'Mepla'


class NotificationManager(object):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')