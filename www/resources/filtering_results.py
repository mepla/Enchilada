__author__ = 'Mepla'


def filter_user_info(user_info):
    user_info_copy = dict(user_info)
    if 'password' in user_info_copy:
        del(user_info_copy['password'])
    if '_id' in user_info_copy:
        del(user_info_copy['_id'])
    if 'id' in user_info_copy:
        del(user_info_copy['id'])
    if 'udid' in user_info_copy:
        del(user_info_copy['udid'])

    return user_info_copy

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
