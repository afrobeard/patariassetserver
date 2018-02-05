import os
import json
import hashlib


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
