__author__ = 'Mepla'

import hmac
import hashlib
import logging


class PasswordManager(object):
    @staticmethod
    def hash_password(p, u):
        if not p or not u:
            logging.error('Can not hash password without 2 arguments.')
            return None

        digest_maker = hmac.new(str(u), str(p), hashlib.sha1)
        return digest_maker.hexdigest()

    @staticmethod
    def compare_passwords(gp, ahp, u):
        if not gp or not u or not ahp:
            logging.error('Can not compare passwords without 3 arguments.')
            return False

        ghp = PasswordManager.hash_password(gp, u)
        return ghp == ahp
