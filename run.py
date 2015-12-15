from www.resources.storage import Storage, StorageAccess
from www.resources.user_followers import UserFollowers
from www.resources.user_followings import UserFollowings

__author__ = 'Mepla'

import logging

from www.resources.sign_up import SignUp
from www.resources.login import Login
from www.resources.users import User, Users
from www.resources.businesses import BusinessProfile, BusinessCategory, Businesses, BusinessAdmins, BusinessAdmin
from www.resources.users_checkin import UsersCheckin
from www.resources.checkin import CheckIn
from www.resources.business_surveys import BusinessSurveyResult, BusinessSurveyTemplate, BusinessSurveyResults, BusinessSurveyTemplates
from www.resources.business_messages import BusinessMessage, BusinessMessages
from www.resources.business_reveiws import BusinessReview, BusinessReviews
from www.resources.business_promotions import BusinessPromotion, BusinessPromotions, EligiblePromotions, PromotionApply
from www.resources.business_followers import BusinessFollowers
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
    api.add_resource(BusinessMessages, '/businesses/<string:bid>/messages')
    api.add_resource(BusinessMessage, '/businesses/<string:bid>/messages/<string:mid>')
    api.add_resource(BusinessReviews, '/businesses/<string:bid>/reviews')
    api.add_resource(BusinessReview, '/businesses/<string:bid>/reviews/<string:rid>')
    api.add_resource(Businesses, '/businesses')
    api.add_resource(BusinessAdmins, '/businesses/<string:bid>/admins')
    api.add_resource(BusinessAdmin, '/businesses/<string:bid>/admins/<string:admin_uid>')
    api.add_resource(BusinessPromotions, '/businesses/<string:bid>/promotions')
    api.add_resource(BusinessPromotion, '/businesses/<string:bid>/promotions/<string:pid>')
    api.add_resource(EligiblePromotions, '/businesses/<string:bid>/promotions/eligible_for_me')
    api.add_resource(PromotionApply, '/businesses/<string:bid>/promotions/<string:pid>/apply')
    api.add_resource(Storage, '/storage')
    api.add_resource(StorageAccess, '/storage/<string:file_id>')

    api.add_resource(BusinessFollowers, '/businesses/<string:bid>/followers')
    api.add_resource(UserFollowers, '/users/<string:target_uid>/followers')
    api.add_resource(UserFollowings, '/users/<string:target_uid>/followings')

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
