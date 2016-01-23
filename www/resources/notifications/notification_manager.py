import collections
import logging
from www.resources.databases.factories import DatabaseFactory
from www.resources.json_schemas import validate_json, JsonValidationException
from www.resources.utilities.helpers import utc_now_timestamp, uuid_with_prefix

__author__ = 'Mepla'


class NotificationManager(object):
    def __init__(self):
        self.doc_db = DatabaseFactory().get_database_driver('document/docs')
        self.notif_settings = {
            'follow_request': {
                'schema': {
                    "type": "object",
                    "properties": {
                        "follower":  {"type": "string"},
                        "followee":  {"type": "string"},
                        "frid":  {"type": "string"},
                        "follower_data":  {"type": "object"}
                    },
                    "additionalProperties": True,
                    "required": ["follower", "followee", "frid", "follower_data"]
                },
                'method': self.create_follow_request_notification
            },

            'follow_accept': {
                'schema': {

                },
                'method': self.create_follow_request_notification
            },

            'sign_up': {
                'schema': {
                    "type": "object",
                    "properties": {
                        "uid":  {"type": "string"},
                        "user":  {
                            "type": "object",
                            'properties': {
                                "name":  {"type": "string"},
                                "lastname":  {"type": "string"},
                                "gender":  {"type": "string"}
                            },
                            "additionalProperties": True,
                            "required": ["name"]
                        }
                    },
                    "additionalProperties": True,
                    "required": ["uid", "user"]
                },
                'method': self.create_sign_up_notification
            },

            'checkin_survey': {
                'schema': {

                },
                'method': self.create_follow_request_notification
            },

            'earn_points': {
                'schema': {

                },
                'method': self.create_follow_request_notification
            },

            'redeem_points': {

            }
        }

    def add_notification(self, notif_type, notif_data, notif_timestamp=None):
        if not notif_timestamp:
            notif_timestamp = utc_now_timestamp()

        try:
            validate_json(notif_data, self.notif_settings.get(notif_type).get('schema'))
        except JsonValidationException as exc:
            raise exc

        method = self.notif_settings.get(notif_type).get('method')
        assert isinstance(method, collections.Callable)
        whole_data = method(notif_data, notif_timestamp)
        try:
            self.doc_db.save(whole_data, 'user_notifications')

        except Exception as exc:
            logging.error('Could not save {} notification: {}'.format(notif_type, exc))
            raise Exception

    def create_follow_request_notification(self, notif_data, notif_timestamp):
        data_to_be_saved = {'follower': notif_data.get('follower'), 'followee': notif_data.get('followee'),
                            'frid': notif_data.get('frid'), 'follower_data': notif_data.get('follower_data')}

        unid = uuid_with_prefix('unid')

        whole_data = {'timestamp': notif_timestamp, 'notification_type': 'follow_request', 'data': data_to_be_saved,
                      'seen': False, 'unid': unid, 'uid': notif_data.get('followee')}

        return whole_data

    def create_sign_up_notification(self, notif_data, notif_timestamp):
        name = notif_data.get('user').get('name')
        lastname = notif_data.get('user').get('lastname')
        gender = notif_data.get('user').get('gender')
        title = ''
        if gender.lower() == 'm':
            title = ' Mr.'
        elif gender.lower() == 'f':
            title = ' Ms.'

        if lastname:
            name += ' ' + lastname

        welcome_message = 'Dear{} {}, Welcome to Echo, You can now checkout different businesses and use Echo\'s ' \
                          'features to discover and support interesting businesses along with earning various points ' \
                          'and bonuses.'.format(title, name)

        data_to_be_saved = {'message': welcome_message}

        unid = uuid_with_prefix('unid')

        whole_data = {'timestamp': notif_timestamp, 'notification_type': 'sign_up', 'data': data_to_be_saved,
                      'seen': False, 'unid': unid, 'uid': notif_data.get('uid')}

        return whole_data
