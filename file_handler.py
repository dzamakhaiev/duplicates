import os
import shutil


def create_file(filename, n_bytes=1000):
    """
    Create file with defined size in bytes
    """
    try:
        with open(filename, 'wb') as file:
            file.truncate(n_bytes)

    except (OSError, PermissionError) as e:
        print(e)


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


def delete_dir(dirname):
    try:
        os.rmdir(dirname)
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


def delete_list_of_dirs(dirs):
    for dirname in dirs:
        delete_dir(dirname)


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
