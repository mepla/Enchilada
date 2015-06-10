__author__ = 'Mepla'

import logging
from resources.sign_up import SignUp
from www import api, app

def initialize_app():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    py2neo_logger = logging.getLogger('httpstream')
    py2neo_logger.setLevel(logging.CRITICAL)

    api.add_resource(SignUp, '/signup')

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
