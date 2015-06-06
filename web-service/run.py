__author__ = 'Mepla'
from flask import Flask
from flask_restful import Resource, Api


class EchoBackendApp(Flask):
    def initialize_app(self, api):
        # api.add_resource()
        pass

if __name__ == '__main__':
    app = EchoBackendApp(__name__)
    api = Api(app)
    app.initialize_app(api)
    app.run(host='0.0.0.0', debug=True)
