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

def filter_general_document_db_record(dic):

    if 'id' in dic:
        del(dic['id'])

    if '_id' in dic:
        del(dic['_id'])

    return dic
