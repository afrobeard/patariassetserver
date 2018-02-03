import os
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


