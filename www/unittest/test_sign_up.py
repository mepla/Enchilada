__author__ = 'Naja'

import unittest
from www import app, api
from www.run import initialize_app
import base64
import json

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.api = api
        initialize_app()

    def tearDown(self):
        pass

    def test_login(self):
        resp = self._login('s@n.com', '123456', 'test_client', 'X_secret_X', 'all')
        resp_data = json.loads(resp.data)
        self.assertIsInstance(resp_data, dict)

    def _login(self, username, password, client_id, client_secret, scope):
        authorization_header = base64.b64encode(client_id + ':' + client_secret)
        return self.app.post('/login?grant_type=password',
                             data={'username': username, 'password': password},
                             headers={'scope': scope, 'Authorization': 'Basic {}'.format(authorization_header),
                                      'Content-Type': 'application/json'})

if __name__ == '__main__':
    unittest.main()
