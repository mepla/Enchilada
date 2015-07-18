__author__ = 'Mepla'

import logging

from resources.sign_up import SignUp
from resources.login import Login
from resources.users import User, Users
from www.resources.businesses import BusinessProfile, BusinessCategory
from www.resources.users_checkin import UsersCheckin
from www.resources.checkin import CheckIn
from www.resources.business_surveys import BusinessSurveyResult, BusinessSurveyTemplate, BusinessSurveyResults, BusinessSurveyTemplates
from www import api, app


def initialize_app():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    py2neo_logger = logging.getLogger('httpstream')
    py2neo_logger.setLevel(logging.CRITICAL)

    api.add_resource(SignUp, '/signup')
    api.add_resource(Login, '/login')
    api.add_resource(BusinessProfile, '/businesses/<string:bid>')
    api.add_resource(CheckIn, '/businesses/<string:bid>/checkins')
    api.add_resource(Users, '/users')
    api.add_resource(User, '/users/<string:user_id>')
    api.add_resource(UsersCheckin, '/users/<string:user_id>/checkins')
    api.add_resource(BusinessCategory, '/businesses/categories')
    api.add_resource(BusinessSurveyResults, '/businesses/<string:bid>/surveys')
    api.add_resource(BusinessSurveyResult, '/businesses/<string:bid>/surveys/<string:survey_id>')
    api.add_resource(BusinessSurveyTemplates, '/businesses/<string:bid>/survey_templates')
    api.add_resource(BusinessSurveyTemplate, '/businesses/<string:bid>/survey_templates/<string:survey_id>')

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
