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

user_put_schema = '''
{
    "type": "object",
    "properties":{
        "f_name":  { "type": "string" },
        "l_name": { "type": "string" },
        "email": { "type": "string" },
        "gender": { "type": "string" },
        "birth_date": { "type": "string" },
        "device": { "type": "string" },
        "udid": { "type": "string" },
        "latitude": { "type": "number" },
        "longitude": { "type": "number" }
    },
    "additionalProperties": false
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

business_signup_schema = '''
{
    "type": "object",
    "properties":{
        "creation_date":  { "type": "string" },
        "name": { "type": "string" },
        "title": { "type": "string" },
        "description": { "type": "string" },
        "category": { "type": "number" },
        "email": { "type": "string" },
        "password": { "type": "string" },
        "latitude": { "type": "number" },
        "longitude": { "type": "number" }
    },
    "additionalProperties": false,
    "required": [ "creation_date","name","title","description","category","email","password","latitude","longitude"]
}
'''

business_app_schema = '''
{
    "type": "object",
    "properties":{
        "bid":  { "type": "string" }
    },
    "additionalProperties": false,
    "required": [ "bid"]
}
'''

business_category_add_single_schema = '''
{
    "type": "object",
    "properties":{
        "name":  { "type": "string" },
        "parent":  { "type": "string" }
    },
    "additionalProperties": false,
    "required": [ "name"]
}
'''

patch_schema = '''
{
    "type": "array",
    "items": {
        "type": "object",
        "properties":{
            "op":  { "type": "string" },
            "path":  { "type": "string" },
            "value":  { "type": "string" }
        },
        "additionalProperties": false,
        "required": [ "op", "path", "value"]
    }
}
'''

survey_result_schema = '''
{
    "type": "object",
    "properties":{
        "stid": { "type": "string" },
        "answers":  {
            "type": "object",
            "properties":{
                "^[0-9]+$": {"type": "string"}
            }
        }
    },
    "additionalProperties": false,
    "required": [ "stid", "answers"]
}
'''

message_schema = '''
{
    "type": "object",
    "properties":{
        "subject":  { "type": "string" },
        "body":  { "type": "string" }
    },
    "additionalProperties": false,
    "required": [ "body"]
}
'''

review_schema = '''
{
    "type": "object",
    "properties":{
        "subject":  { "type": "string" },
        "body":  { "type": "string" },
        "rating":  { "type": "integer" }
    },
    "additionalProperties": false,
    "required": [ "body"]
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
