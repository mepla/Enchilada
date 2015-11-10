__author__ = 'Mepla'

import hmac
import hashlib
import logging


class PasswordManager(object):
    @staticmethod
    def hash_password(p, u, e):
        if not p or not u or not e:
            logging.error('Can not hash password without 3 arguments.')
            return None

        digest_maker = hmac.new(str(u + e), str(p), hashlib.sha1)
        return digest_maker.hexdigest()

    @staticmethod
    def compare_passwords(gp, ahp, u, e):
        if not gp or not u or not e or not ahp:
            logging.error('Can not compare passwords without 4 arguments.')
            return False

        ghp = PasswordManager.hash_password(gp, u, e)
        return ghp == ahp
