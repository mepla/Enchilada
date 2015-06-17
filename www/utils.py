__author__ = 'Mepla'

import re

def check_email_format(email):
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)
