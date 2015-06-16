__author__ = 'Mepla'

import json
import logging
from jsonschema import validate


class JsonValidationException(Exception):
    pass

signup_schema = '''
{
    "type": "object",
    "properties":{
        "f_name":  { "type": "string" },
        "l_name": { "type": "string" },
        "email": { "type": "string" },
        "password": { "type": "string" },
        "gender": { "type": "string" },
        "birth_date": { "type": "string" },
        "device": { "type": "string" },
        "udid": { "type": "string" },
        "latitude": { "type": "number" },
        "longitude": { "type": "number" }
    },
    "additionalProperties": false,
    "required": [ "f_name", "l_name", "email", "password", "udid" ]
}
'''

login_schema = '''
{
    "type": "object",
    "properties":{
        "username":  { "type": "string" },
        "password": { "type": "string" }
    },
    "additionalProperties": false,
    "required": [ "username", "password"]
}
'''



def validate_json(json_data, schema):
    try:
        if isinstance(schema, str):
            schema = json.loads(schema)
        validate(json_data, schema)
    except Exception as exc:
        logging.error('Error validating json: {} --> {}'.format(type(exc), exc.message))
        raise JsonValidationException(exc.message)