import os
import json
import hashlib
import random as rnd
from azure.storage.blob import BlockBlobService
from patariassetserver import settings


def get_size(file_path):
    try:
        return os.stat(file_path).st_size
    except FileNotFoundError as e:
        raise FileNotFoundError(e)


def get_checksum(file_path, block_size=2**20):
    try:
        tmp_file = open(file_path, 'rb')
        hash = hashlib.md5()

        while True:
            data = tmp_file.read(block_size)
            if not data:
                break
            hash.update(data)
            return hash.hexdigest()
    except FileNotFoundError as e:
        raise FileNotFoundError(e)
    except IOError as e:
        raise FileNotFoundError(e)


def make_error_obj_from_validation_error(ve):
    err_obj = {
        "error_message": "Invalid form.",
        "error_details": ve.messages if hasattr(ve, 'error_list') else [],
        "validation_errors": []
    }
    if hasattr(ve, 'error_dict'):
        for k, v in ve.message_dict.items():
            if k == '__all__':
                err_obj['error_details'] += v
            else:
                # TODO: do this in the proper generic Right Way (TM)
                if v and v[0].startswith('{"'):
                    subfield_error_dict = json.loads(v[0])
                    for itemidx, subdict in subfield_error_dict.items():
                        for subfieldname, suberrorlist in subdict.items():
                            err_obj['validation_errors'].append({
                                "field": "{}[{}].{}".format(k, itemidx, subfieldname),
                                "errors": suberrorlist
                            })
                else:
                    err_obj['validation_errors'].append({
                        "field": k,
                        "errors": v
                    })
    return err_obj


def get_random_string():
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"
    string_length = 8
    randomstring = ''
    for i in range(0, string_length):
        rnum = int(rnd.random() * len(chars))
        randomstring += chars[rnum: rnum + 1]
    return randomstring


def upload_image_to_azure(blob_name, file_path):

    print("uploading:" + blob_name + " from " + file_path)

    block_blob_service = BlockBlobService(account_name=settings.AZURE_ACCOUNT_NAME,
                                          account_key=settings.AZURE_ACCOUNT_KEY)

    try:
        block_blob_service.create_blob_from_path(container_name=settings.AZURE_CONTAINER_NAME,
                                                 blob_name=blob_name,
                                                 file_path=file_path)
    except Exception as e:
        print(e)
        return False
    return True
