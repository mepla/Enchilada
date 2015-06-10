__author__ = 'Mepla'


import json
import logging
from flask import Flask, jsonify
from flask_restful import Api
from www.config import default_configs, config_path

app = Flask(__name__)
api = Api(app)

# @app.errorhandler(Exception)
def all_exception_response(e):
    return jsonify({'message': 'Internal server error. There is nothing you can do at this moment.'}), 500



try:
    configs = json.load(config_path)
except Exception as exc:
    logging.warning('Could not load config file ({}). Default configs loaded.'.format(config_path))
    configs = default_configs
