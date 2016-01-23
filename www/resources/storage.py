from flask_restful import Resource
from www import oauth2, app
from www.resources.config import configs
from www.resources.utilities.helpers import uuid_with_prefix

__author__ = 'Mepla'


import os

import logging
from flask import request, make_response, jsonify
from flask.helpers import send_from_directory


class Storage(Resource):

    @oauth2.check_access_token
    def post(self, uid=None):
        filename = uuid_with_prefix('f')

        uploaded_file = None
        for file_key in request.files.keys():
            uploaded_file = request.files.get(file_key)

        if not uploaded_file:
            msg = 'You have not sent a file, a file must be attached.'
            logging.error(msg)
            return make_response(jsonify({'message': msg}), 400)

        directory = configs['STORAGE']['STORAGE_PATH']
        directory = directory.rstrip('/') + '/' + uid

        if not os.path.exists(directory):
            try:
                os.mkdir(directory)
            except Exception as exc:
                logging.info('Path does not exist for UPLOAD_FOLDER: {}'.format(directory))
                return make_response(jsonify({'message': 'Internal server error.'}), 500)

        try:
            (file_category, file_format) = uploaded_file.mimetype.split('/')
        except Exception as exc:
            logging.info('Could not parse mimetype of file.')
            return make_response(jsonify({'message': 'Uploaded file must have a content-type (Mimetype).'}), 400)

        logging.info('File received: %s/%s', file_category, file_format)

        if file_category == 'image':
            uploaded_file.save(os.path.join(directory, filename))

        else:
            return make_response(jsonify({'message': 'Your file is not supported, please read the documentation and '
                                                    'send an appropriate file.'}), 400)

        if os.path.isfile(directory + '/' + filename):
            return {"path": "/storage/" + filename}
        else:
            return make_response(jsonify({'message': 'Failed to convert sent file, check you time and try again.'}), 400)


class StorageAccess(Resource):

    @oauth2.check_access_token
    def get(self, file_id, uid=None):

        logging.debug('User ({}) requested file: {}'.format(uid, file_id))

        parent_dir = self._find_doc(file_id, uid)

        if not parent_dir:
            return make_response(jsonify({'message': 'The file you requested does not exits.'}), 404)
        else:
            return send_from_directory(parent_dir, file_id, as_attachment=True)

    def _find_doc(self, file_id, uid):
        directory = configs['STORAGE']['STORAGE_PATH']
        directory = directory.rstrip('/') + '/'
        sub_directory = directory + uid
        full_path = sub_directory + '/' + file_id

        if not os.path.isfile(full_path):
            for (path, dirs, files) in os.walk(directory):
                if file_id in files:
                    return path
        else:
            return sub_directory

        return None
