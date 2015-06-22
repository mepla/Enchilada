__author__ = 'Mepla'

import logging
import pprint
from uuid import uuid4
from flask import request
from flask_restful import Resource
from www import utils
from www.authentication import password_management as pm
from www.resources.json_schemas import validate_json, JsonValidationException, signup_schema
from www.databases.factories import DatabaseFactory

number_of_allowed_users_with_udid = 3

class SignUp(Resource):
    def __init__(self):
        super(SignUp, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    def post(self):
        logging.info('Client requested for sign up.')

        try:
            data = request.get_json(force=True)
        except Exception as exc:
            msg = {'msg': exc.message}
            logging.error(msg)
            return msg, 400

        try:
            validate_json(body, signup_schema)
            logging.info('Client requested for sign up with payload: \n{}'.format(pprint.pformat(body)))
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.debug(msg)
            return msg, 400

        email = body.get('email')
        if not utils.check_email_format(email):
            msg = {'message': 'The email address you entered is invalid.'}
            logging.error(msg)
            return msg, 400

        user_exists = self.graph_db.find_user(email)

        if user_exists:
            msg = {'message': 'A user is already registered with this email address: {}'.format(email)}
            logging.debug(msg)
            return msg, 400

        udid = body.get('udid')
        more_than_max_udid = self.graph_db.users_with_udid(udid) >= number_of_allowed_users_with_udid

        if more_than_max_udid:
            msg = {'message': 'More than {} users are signed up with this udid: {}'
                .format(number_of_allowed_users_with_udid, udid)}

            logging.debug(msg)
            return msg, 400

        body['uid'] = uuid4().hex
        hashed_password = pm.PasswordManager.hash_password(body['password'], body['uid'], body['email'])
        body['password'] = hashed_password

        return self.graph_db.create_new_user(**body)
