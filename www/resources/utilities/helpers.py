import uuid
import re
import datetime

__author__ = 'Mepla'


class PatchError(Exception):
    pass


class PatchReadOnlyViolation(PatchError):
    pass


class PatchExcessiveAddViolation(PatchError):
    pass


class PatchTypeViolation(PatchError):
    pass


def _filter_single_general_document_db_record(doc, doc_type=None):

    if 'id' in doc:
        del(doc['id'])

    if '_id' in doc:
        del(doc['_id'])

    if doc_type and isinstance(doc_type, (str, unicode)):
        doc['type'] = doc_type
    return doc


def filter_general_document_db_record(doc, doc_type=None):
    if isinstance(doc, dict):
        return _filter_single_general_document_db_record(doc, doc_type)
    if isinstance(doc, list):
        return_list = []
        for single_doc in doc:
            return_list.append(_filter_single_general_document_db_record(single_doc, doc_type))
        return return_list


def _filter_single_user_info(doc, include_doc_type=False):
    user_info_copy = dict(doc)
    user_info_copy = filter_general_document_db_record(user_info_copy)
    assert isinstance(user_info_copy, dict)

    if 'password' in user_info_copy:
        del(user_info_copy['password'])

    if 'udid' in user_info_copy:
        del(user_info_copy['udid'])

    if include_doc_type:
        user_info_copy['type'] = 'user'

    return user_info_copy


def filter_user_info(user_info, include_doc_type=False):
    if isinstance(user_info, dict):
        return _filter_single_user_info(user_info, include_doc_type)
    if isinstance(user_info, list):
        return_list = []
        for single_doc in user_info:
            return_list.append(_filter_single_user_info(single_doc, include_doc_type))
        return return_list


def uuid_with_prefix(prefix):
    if not prefix:
        prefix = ''
    return str(prefix) + uuid.uuid4().hex


def check_email_format(email):
    return re.match(r'[^@]+@[^@]+\.[^@]+', email)


def date_now_formatted():
    return date_formatted(datetime.datetime.utcnow())


def date_formatted(date):
    return date.strftime('%Y-%m-%d %H:%M:%S')


def utc_now_timestamp():
    return timestamp_from_date(datetime.datetime.utcnow())


def timestamp_from_date(date):
    return (date - datetime.datetime(1970, 1, 1, 0, 0, 0, 0)).total_seconds()


def convert_str_query_string_to_bool(query_str, default=False):
    if not query_str:
        return default

    query_str = str(query_str)
    query_str_low = query_str.lower()
    if query_str_low == 'true' or query_str_low == '1':
        return True
    else:
        return False


class Patch(object):
    @staticmethod
    def patch_doc(patch_array, doc, read_only_paths):
        new_doc = dict(doc)
        for operation in patch_array:
            op = operation['op']
            path = operation['path']
            value = operation['value']

            if path in read_only_paths:
                raise PatchReadOnlyViolation({})

            if op == 'replace':
                pass
            elif op == 'add':
                pass
            elif op == 'remove':
                pass
