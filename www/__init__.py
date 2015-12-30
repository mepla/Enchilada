from www.resources.databases.db_helpers import DBHelper

__author__ = 'Mepla'

from flask import Flask, jsonify
from flask_restful import Api
from flask_httpauth import HTTPBasicAuth

from www.resources.config import default_configs, config_path
from www.resources.authentication.oauth2 import OAuth2Provider

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()
oauth2 = OAuth2Provider()
db_helper = DBHelper()


# @app.errorhandler(Exception)
def all_exception_response(e):
    return jsonify({'message': 'Internal server error. There is nothing you can do at this moment.'}), 500


# @app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'URL Not found!'}), 404

