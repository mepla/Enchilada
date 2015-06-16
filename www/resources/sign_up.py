__author__ = 'Mepla'

import logging
import pprint

from flask import request
from flask_restful import Resource

from www.resources.json_schemas import validate_json, JsonValidationException, signup_schema
from www.databases.factories import DatabaseFactory

number_of_allowed_users_with_udid = 3

class SignUp(Resource):
    def __init__(self):
        super(SignUp, self).__init__()
        self.graph_db = DatabaseFactory().get_database_driver('graph')

    def post(self):
        logging.info('Client requested for sign up.')
        body = request.get_json(force=True)

        try:
            validate_json(body, signup_schema)
            logging.info('Client requested for sign up with payload: \n{}'.format(pprint.pformat(body)))
        except JsonValidationException as exc:
            msg = {'message': exc.message}
            logging.debug(msg)
            return msg, 400

        email = body.get('email')
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

        return self.graph_db.create_new_user(**body)
