__author__ = 'Mepla'

import logging

from resources.sign_up import SignUp
from resources.login import Login
from resources.users import User, Users
from www.resources.business_app_profile import BusinessProfile
from www.resources.checkin import CheckIn
from www import api, app


def initialize_app():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    py2neo_logger = logging.getLogger('httpstream')
    py2neo_logger.setLevel(logging.CRITICAL)

    api.add_resource(SignUp, '/signup')
    api.add_resource(Login, '/login')
    # *** Business Profile ***
    api.add_resource(BusinessProfile, '/business/<string:bid>')
    api.add_resource(CheckIn, '/businesses/<string:bid>/checkins')
    api.add_resource(Users, '/users')
    api.add_resource(User, '/users/<string:user_id>')

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', debug=True)
