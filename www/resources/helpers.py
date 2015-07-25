import uuid

__author__ = 'Mepla'


class PatchError(Exception):
    pass


class PatchReadOnlyViolation(PatchError):
    pass


class PatchExcessiveAddViolation(PatchError):
    pass


class PatchTypeViolation(PatchError):
    pass


def filter_single_general_document_db_record(doc):

    if 'id' in doc:
        del(doc['id'])

    if '_id' in doc:
        del(doc['_id'])

    return doc


def filter_general_document_db_record(doc):
    if isinstance(doc, dict):
        return filter_single_general_document_db_record(doc)
    if isinstance(doc, list):
        return_list = []
        for single_doc in doc:
            return_list.append(filter_single_general_document_db_record(single_doc))
        return return_list


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


def uuid_with_prefix(prefix):
    if not prefix:
        prefix = ''
    return str(prefix) + uuid.uuid4().hex
