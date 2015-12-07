from flask_restful import Resource
from www import oauth2, app
from www.resources.config import configs

__author__ = 'Mepla'


import os
import uuid

import logging
from flask import request, make_response, jsonify
from flask.helpers import send_from_directory


class Storage(Resource):

    @oauth2.check_access_token
    def post(self, uid=None):
        filename = str(uuid.uuid4().hex)

        uploaded_file = None
        for file_key in request.files.keys():
            uploaded_file = request.files.get(file_key)

        if not uploaded_file:
            msg = 'You have not sent a file, a file must be attached.'
            logging.error(msg)
            return make_response(jsonify({'reason': msg}), 400)

        directory = configs['STORAGE']['STORAGE_PATH']
        directory = directory.rstrip('/') + '/' + uid

        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except Exception as exc:
                logging.info('Path does not exist for UPLOAD_FOLDER: {}'.format(directory))
                return make_response(jsonify({'reason': 'Internal server error.'}), 500)

        try:
            (file_category, file_format) = uploaded_file.mimetype.split('/')
        except Exception as exc:
            logging.info('Could not parse mimetype of file.')
            return make_response(jsonify({'reason': 'Uploaded file must have a content-type (Mimetype).'}), 400)

        logging.info('File received: %s/%s', file_category, file_format)

        if file_category == 'image':
            uploaded_file.save(os.path.join(directory, filename))

        else:
            return make_response(jsonify({'reason': 'Your file is not supported, please read the documentation and '
                                                    'send an appropriate file.'}), 400)

        if os.path.isfile(directory + '/' + filename):
            return {"path": "/storage/" + filename}
        else:
            return make_response(jsonify({'reason': 'Failed to convert sent file, check you time and try again.'}), 400)


class StorageAccess(Resource):

    @oauth2.check_access_token
    def get(self, file_id, uid=None):
        directory = configs['STORAGE']['STORAGE_PATH']
        directory = directory.rstrip('/') + '/' + uid
        
        if not os.path.isfile(directory + '/' + file_id):
            return make_response(jsonify({'reason': 'The file you requested does not exits.'}), 404)
        else:
            return send_from_directory(directory, file_id, as_attachment=True)
