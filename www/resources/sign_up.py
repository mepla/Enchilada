from www.resources.notifications.notification_manager import NotificationManager

__author__ = 'Mepla'

import logging
import pprint

from flask import request

from flask_restful import Resource

from www.resources.utilities.helpers import uuid_with_prefix, check_email_format
from www.resources.authentication import password_management as pm
from www.resources.json_schemas import validate_json, JsonValidationException, signup_schema
from www.resources.databases.factories import DatabaseFactory
from www.resources.databases.database_drivers import DatabaseRecordNotFound
from www.resources.users import filter_user_info

number_of_allowed_users_with_udid = 100


class SignUp(Resource):
    def __init__(self):
        super(SignUp, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')
        self.notification_manager = NotificationManager()

    def post(self):
        logging.info('Client requested for sign up.')

        try:
            logging.debug('data: {}\nheaders: {}'.format(request.data, request.headers))
            body = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': 'Your JSON is invalid.',
                   'error': 'bad_input'}
            logging.error(msg)
            return msg, 400

        return self.sign_up_user(body)

    def sign_up_user(self, body, additional_resposibilities=None):
        try:
            validate_json(body, signup_schema)
            logging.debug('Client requested for sign up with payload: \n{}'.format(pprint.pformat(body)))
        except JsonValidationException as exc:
            msg = {'message': exc.message,
                   'error': 'wrong_input'}
            logging.debug(msg)
            return msg, 400

        email = body.get('email')
        if not check_email_format(email):
            msg = {'message': 'The email address you entered is invalid.',
                   'error': 'invalid_email'}
            logging.error(msg)
            return msg, 400

        email = email.lower()

        try:
            user_exists = self.graph_db.find_single_user('email', email)
        except DatabaseRecordNotFound:
            user_exists = False

        if user_exists:
            msg = {'message': 'A user is already registered with this email address: {}'.format(email),
                   'error': 'already_registered'}
            logging.debug(msg)
            return msg, 400

        udid = body.get('udid')
        more_than_max_udid = self.graph_db.users_with_udid_count(udid) >= number_of_allowed_users_with_udid

        if more_than_max_udid:
            msg = {'message': 'More than {} users are signed up with this udid: {}'.
                format(number_of_allowed_users_with_udid, udid),
                   'error': 'excessive_udid'}

            logging.debug(msg)
            return msg, 400

        body['user_type'] = 'personal'
        body['uid'] = uuid_with_prefix('uid')
        body['responsible_for'] = body['uid']
        if additional_resposibilities and len(additional_resposibilities) > 0:
            body['responsible_for'] += ' ' + ' '.join(additional_resposibilities)
        hashed_password = pm.PasswordManager.hash_password(body['password'], body['uid'], body['email'])
        body['password'] = hashed_password

        body['phone'] = ''
        body['echo_number'] = self._generate_echo_number()
        body['settings'] = {
            "privacy_settings": {
                "private_checkins": False,
                "private_profile": False,
                "private_reviews": False
            }
        }
        body['hruid'] = self._generate_hruid()
        body['metrics'] = {
            "followers_count": 0,
            "followings_count": 0,
            "chosen_reviews_count": 0
        }

        created_user = self.graph_db.create_new_user(**body)
        uid = created_user.get('uid')

        try:
            self.graph_db.follow(uid, uid)
            self.graph_db.follow('echomybiz', uid)
        except DatabaseRecordNotFound:
            msg = {'message': 'The user you tried to follow does not exist.',
                   'error': 'internal_server_error'}
            logging.debug(msg)
            return msg, 500

        self.notification_manager.add_notification('sign_up', {'uid': uid, 'user': created_user})

        return filter_user_info(created_user)

    def _generate_echo_number(self):
        return ''

    def _generate_hruid(self):
        return ''
