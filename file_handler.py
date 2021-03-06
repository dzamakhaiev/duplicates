import os
import json
import shutil
import random


def create_file(filename, n_bytes=1000):
    """
    Create file with defined size in bytes
    """
    try:
        with open(filename, 'wb') as file:
            file.truncate(n_bytes)

    except (OSError, PermissionError) as e:
        print(e)


def create_files(filename, n=5, n_bytes=1000, random_size=False):
    """
    Create n files with same/random size
    :param str filename:
    :param int n: number of files
    :param int n_bytes: file size
    :param bool random_size: random size of file
    :return: list of created files
    """
    files = []

    for i in range(1, n + 1):
        name, ext = filename.split('.')
        name += '_{}.{}'.format(i, ext)
        files.append(name)
        size = random.randint(1, n_bytes) if random_size else n_bytes
        create_file(filename=name, n_bytes=size)

    return files


def copy_file(filename, n=1):
    """
    Copy exists file with +1 int the name, starting from 1.
    Does not suppose to make a number of copies more than 9.
    :param str filename:
    :param int n: number of copies
    """
    copies = []
    new_name = None
    last_index = -5
    digit = int(filename[last_index]) + 1 if str.isdigit(filename[last_index]) else 1

    for _ in range(n):

        # first time in loop and first copy
        if not new_name and digit == 1:
            new_name, ext = filename.split('.')
            new_name += '_{}.{}'.format(digit, ext)
            copies.append(new_name)

        # first time in loop and not first copy
        if not new_name and digit > 1:
            new_name = filename.replace(str(digit-1), str(digit))
            digit += 1

        else:
            new_name = new_name.replace(str(digit-1), str(digit))
            copies.append(new_name)
            digit += 1

        try:
            shutil.copyfile(src=filename, dst=new_name)

        except (OSError, PermissionError) as e:
            print(e)

    return copies


def create_dir(dirname):
    try:
        os.mkdir(dirname)
    except (OSError, PermissionError) as e:
        print(e)


def delete_file(filename):
    try:
        os.remove(filename)
    except (OSError, PermissionError) as e:
        print(e)


def delete_dir_recursively(dirname):
    try:
        shutil.rmtree(dirname)
    except (OSError, PermissionError) as e:
        print(e)


def delete_list_of_files(files):
    for filename in files:
        delete_file(filename)


def create_file_structure(file_structure):
    created_files = []
    created_dirs = []

    for directory, files in file_structure.items():
        create_dir(directory)
        created_dirs.append(directory)

        for filename, n_bytes in files.items():
            filename = os.path.join(directory, filename)
            create_file(filename=filename, n_bytes=n_bytes)
            created_files.append(filename)

    return created_files, created_dirs


def read_json_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)

    except (OSError, PermissionError) as e:
        print(e)
