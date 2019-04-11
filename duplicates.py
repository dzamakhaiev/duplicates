#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import time
import json
import logging
import args_parser
from collections import OrderedDict
from copy import deepcopy


TARGET_DIR = r"C:\Program Files (x86)\Steam"
BLOCK_SIZE = 65536
MAX_FILES = 10000
PROCESSES = 2
SIZE_UNIT = "MB"
RESULTS_FILE = "results.txt"
LOG_FILE = "log.txt"
QUIET = False
VERBOSE = True
DEFAULT_ALG = "sha1"
UNITS = {"KB": (1, "kilobytes"), "MB": (2, "megabytes"), "GB": (3, "gigabytes"), "TB":  (4, "terabytes")}

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
if len(sys.argv) > 1:
    USER_ARGS = args_parser.parser.parse_args()
    handler = logging.FileHandler(USER_ARGS.log)
else:
    handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def measure_execution(section):
    # Measure time of execution and save in self var

    def outer_wrapper(func):
        def wrapper(self, *args, **kwargs):
            start = time.time()
            result = func(self, *args, **kwargs)
            self.timing[section] = round(time.time() - start, 1)
            return result

        return wrapper
    return outer_wrapper


class Files:
    """
    This class works with filesystem
    """

    def __init__(self, top_dir=TARGET_DIR, max_files=MAX_FILES):
        self.top_dir = top_dir
        self.max_files = max_files

    def find(self, top=None, max_files=None):
        """
        Find all files in directory. Limited by max_files
        """
        if not top:
            top = self.top_dir
        if not max_files:
            max_files = self.max_files

        files = {}
        counter = 0

        try:
            for result in os.walk(top=top):
                current_dir, included_dirs, included_files = result

                # Collect found files to dict and save file size
                for f in included_files:
                    f_path = os.path.join(current_dir, f)

                    if os.path.isfile(f_path):
                        files.update({f_path: {"f_size": self.get_file_size(f_path)}})
                        counter += 1

                    if counter >= max_files: break
                if counter >= max_files: break

        except (OSError, PermissionError) as e:
            logger.error(msg=e)

        return files

    def find_equal_files(self, files):
        """
        Get list of files with equal size
        """
        equal_files = []
        file_sizes = self.get_files_sizes(files)

        for f_path, f_meta in files.items():
            if f_meta and f_meta.get('f_size') and file_sizes.count(f_meta['f_size']) > 1:
                equal_files.append(f_path)

        equal_files.sort()
        return equal_files

    @staticmethod
    def get_file_size(f_path):
        try:
            return os.path.getsize(f_path)
        except OSError as e:
            logger.error(msg=e)
            return 0

    @staticmethod
    def get_files_sizes(files):
        """
        Get list with sizes of all checked files
        """
        file_sizes = []
        for f_meta in files.values():
            if f_meta and f_meta.get("f_size"):
                file_sizes.append(int(f_meta["f_size"]))

        file_sizes.sort()
        return file_sizes

    @staticmethod
    def write_dict_to_file(results, filename):
        """
        Write dictionary with results to output file
        """
        try:
            with open(filename, 'a+') as results_file:
                json.dump(results, results_file)
                results_file.write("\n")

        except (OSError, PermissionError) as e:
            logger.info(msg=e)


class Hashes:
    """
    Class calculates hashes for files and for stores them
    """

    def __init__(self, alg=DEFAULT_ALG):
        self.alg = alg

    def get_hash_of_file(self, f_path, alg=None):
        """
        Open file, calculate hash of file and return it if it exists
        """
        if not alg:
            alg = self.alg
        hasher = getattr(hashlib, alg, hashlib.sha1)()

        try:
            with open(f_path, 'rb') as f_file:
                for buf in f_file:
                    hasher.update(buf)
            return hasher.hexdigest()

        except (PermissionError, OSError) as e:
            logger.error(msg=e)
            return None

    @staticmethod
    def add_hash(hashes, f_hash, f_path):
        """
        Add hash in dict. If it exists - add new path to this hash
        """
        if f_hash in hashes:
            hashes[f_hash]['f_paths'].append(f_path)
            paths = set(hashes[f_hash]['f_paths'])  # remove duplicated paths just in case
            paths = list(paths)
            paths.sort()
            hashes[f_hash]['f_paths'] = paths
        else:
            hashes.update({f_hash: {'f_paths': [f_path]}})

    def calculate_hashes(self, equal_files):
        """
        Calculate hashes for all files in list
        """
        hashes = {}

        for f_path in equal_files:
            f_hash = self.get_hash_of_file(f_path)
            self.add_hash(hashes=hashes, f_hash=f_hash, f_path=f_path)

        return hashes


class Duplicates:
    """
    Class for finding duplicated files in filesystem using hash of file.
    """

    def __init__(self, args=None):
        # Store console args
        self.args = args

        # Init main instances
        self.files = {}
        self.equal_files = []
        self.hashes = {}
        self.duplicates = {}
        self.results = OrderedDict()

        # Init time measuring dict
        self.timing = {}

        # Set up unit of measuring
        self.unit = self.args.unit if self.args else SIZE_UNIT
        self.degree = UNITS[self.args.unit.upper()][0] if self.args else UNITS[SIZE_UNIT][0]

        # Create and init Files object
        top_dir = self.args.path if self.args else TARGET_DIR
        max_files = self.args.max if self.args else MAX_FILES
        self.top_dir = top_dir
        self.files_obj = Files(top_dir=top_dir, max_files=max_files)

        # Create and init Hashes object
        alg = self.args.alg if self.args else DEFAULT_ALG
        self.alg = alg
        self.hashes_obj = Hashes(alg=alg)

    def convert_bytes_to(self, n_bytes, degree=None):
        """
        Convert bytes to kb, mb, gb, tb. Keep passing var outside for unittests
        :param int n_bytes: bytes to convert
        :param int degree: defined degree for conversion
        :return: converted file size
        """
        if not degree:
            degree = self.degree
        return round(n_bytes / (1024 ** degree), 2)

    @measure_execution(section='Scanning time')
    def find_all_files(self, top_dir=None, max_files=None):
        """
        Find all files in target directory using Files object.
        Keep passing vars and returning result for unit tests
        """
        logger.info(msg='Start scanning the directory: {}'.format(self.args.path if self.args else TARGET_DIR))

        if not top_dir or not max_files:
            files = self.files_obj.find()
        else:
            files = self.files_obj.find(top=top_dir, max_files=max_files)

        logger.info(msg='Complete scanning the directory')
        self.files = deepcopy(files)
        return files

    @measure_execution(section='Checking time')
    def check_all_files(self, files=None):
        """
        Check all found files(using Files object) and store all equal files by size.
        Keep passing var and returning result for unit tests
        """
        if not files:
            files = self.files

        logger.info(msg='Start checking found files for equal size')
        equal_files = self.files_obj.find_equal_files(files=files)
        logger.info(msg='Complete checking found files')

        self.equal_files = equal_files.copy()
        return equal_files

    @measure_execution(section='Hashing time')
    def get_files_hashes(self, equal_files=None):
        """
        Get hashes for all found equal files(using Hashes object) and store it.
        Keep passing var and returning result for unit tests
        """
        logger.info(msg='Start calculating hashes')

        if not equal_files:
            equal_files = self.equal_files

        hashes = self.hashes_obj.calculate_hashes(equal_files=equal_files)
        logger.info(msg='Complete calculating hashes')
        self.hashes = deepcopy(hashes)
        return hashes

    @measure_execution(section='Finding time')
    def find_duplicates(self, hashes=None):
        """
        Find duplicates in hashes dict. Duplicated hash has more than one file path.
        Keep passing vars and returning result for unit tests
        """
        logger.info(msg='Start finding equal files by hash')

        if not hashes:
            hashes = self.hashes
        duplicates = {}

        for f_hash, paths in hashes.items():

            if len(paths['f_paths'][1:]):
                f_size = self.get_file_size(paths['f_paths'])
                duplicates.update({f_hash: {'f_paths': paths['f_paths'], 'f_size': f_size}})

        logger.info(msg='Complete finding equal files')
        self.duplicates = deepcopy(duplicates)
        return duplicates

    def get_file_size(self, f_paths):
        """
        Try to get file size files dict or directly from OS. Because all files in list have equal size,
        it's normal to get any of them.
        """
        for f_path in f_paths:
            if f_path in self.files.keys() and self.files[f_path]['f_size']:
                return self.files[f_path]['f_size']

        for f_path in f_paths:
            f_size = self.files_obj.get_file_size(f_path)
            if f_size:
                return f_size

        return 0

    def get_scanned_size(self, files=None):
        """
        Get size of all scanned files in target directory.
        Keep passing var and returning result for unit tests
        """
        if not files:
            files = self.files

        scanned_size = sum([int(f_meta.get('f_size')) for f_meta in files.values() if f_meta.get('f_size')])
        scanned_size = self.convert_bytes_to(scanned_size)
        return scanned_size

    def get_hashed_size(self, hashes=None):
        """
        Get size of all hashed files.
        Keep passing var and returning result for unit tests
        """
        if not hashes:
            hashes = self.hashes

        hashed_size = 0
        for h_meta in hashes.values():
            f_size = self.get_file_size(f_paths=h_meta['f_paths'])
            hashed_size += len(h_meta['f_paths']) * f_size

        hashed_size = self.convert_bytes_to(hashed_size)
        return hashed_size

    def get_duplicates_size(self, duplicates=None):
        """
        Get size of all duplicated files.
        Keep passing var and returning result for unit tests
        """
        if not duplicates:
            duplicates = self.duplicates

        duplicated_size = 0
        for f_meta in duplicates.values():

            f_paths, f_size = f_meta.get('f_paths'), f_meta.get('f_size')
            if f_size:
                duplicated_size += (len(f_paths) - 1) * f_size
            else:
                duplicated_size += (len(f_paths) - 1) * self.get_file_size(f_paths)

        duplicated_size = self.convert_bytes_to(duplicated_size)
        return duplicated_size

    def calculate_results(self):
        """
        Aggregate results of check in dict
        """
        logger.debug(msg='Calculating results')
        self.results.update({"Target directory": self.top_dir})
        self.results.update({"Files found": self.files.__len__()})
        self.results.update({"Scanned files size": "{} {}".format(self.get_scanned_size(), self.unit)})
        self.results.update({"Scanning time": "{} sec".format(self.timing.get('Scanning time', 0))})
        self.results.update({"Checking time": "{} sec".format(self.timing.get('Checking time', 0))})
        self.results.update({"Files hashed": self.hashes.__len__()})
        self.results.update({"Hashed files size": "{} {}".format(self.get_hashed_size(), self.unit)})
        self.results.update({"Hashing time": "{} sec".format(self.timing.get('Hashing time', 0))})
        self.results.update({"Duplicates found": self.duplicates.__len__()})
        self.results.update({"Duplicates size": "{} {}".format(self.get_duplicates_size(), self.unit)})
        self.results.update({"Finding time": "{} sec".format(self.timing.get('Finding time', 0))})
        self.results.update({"Total time": "{} sec".format(round(sum(self.timing.values()), 2))})
        self.results.update({"Algorithm": self.alg})

    def show_results_in_console(self):
        logger.info(msg='Show results in console')
        for key, value in self.results.items():
            print("{}: {}".format(key, value))
            logger.debug(msg="{}: {}".format(key, value))

    def show_duplicates_in_console(self):
        logger.info(msg='Show duplicates in console')
        for _, f_meta in self.duplicates.items():
            print('=' * 50)
            print('\n'.join([f_path for f_path in f_meta['f_paths']]))

            f_size = f_meta['f_size']
            f_size = round(f_size / (1024 ** self.degree), 2)
            duplicated_size = (len(f_meta['f_paths']) - 1) * f_size
            duplicated_size = round(duplicated_size, 2)
            total_str = 'File size: {0} {2}. Total size of duplicated files: {1} {2}'
            total_str = total_str.format(f_size, duplicated_size, self.unit)

            print(total_str)
            logger.debug(msg=total_str)

    def show_results(self):
        """
        Show results in console if flags allow that
        """
        if self.args and not self.args.quiet:
            self.show_results_in_console()

        elif not self.args and not QUIET:
            self.show_results_in_console()

        if self.args and not self.args.quiet and self.args.verbose:
            self.show_duplicates_in_console()

        elif not self.args and not QUIET and VERBOSE:
            self.show_duplicates_in_console()

    def write_results(self, results=None, results_file=None):
        """
        Write results dict to output file
        """
        if not results:
            results = self.results

        if not results_file:
            results_file = self.args.output if self.args else RESULTS_FILE

        self.files_obj.write_dict_to_file(results=results, filename=results_file)


if __name__ == '__main__':

    # user mode
    if len(sys.argv) > 1:
        duplicates_obj = Duplicates(args=args_parser.parser.parse_args())

    # debug mode
    else:
        duplicates_obj = Duplicates()

    duplicates_obj.find_all_files()
    duplicates_obj.check_all_files()
    duplicates_obj.get_files_hashes()
    duplicates_obj.find_duplicates()
    duplicates_obj.calculate_results()
    duplicates_obj.show_results()
    duplicates_obj.write_results()
