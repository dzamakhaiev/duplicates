#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import time
import json
import logging
import args
from multiprocessing import Pool
from collections import OrderedDict
from copy import deepcopy


TARGET_DIR = r"C:\Program Files (x86)\Steam"
BLOCK_SIZE = 65536
MAX_FILES = 10000
PROCESSES = 2
SIZE_UNIT = "GB"
RESULTS_FILE = "results.txt"
LOG_FILE = "log.txt"
DEFAULT_ALG = "sha1"
UNITS = {"MB": (2, "megabytes"), "GB": (3, "gigabytes"), "TB":  (4, "terabytes")}

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("log.txt")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Hash:

    def __init__(self, alg=DEFAULT_ALG):
        self.hash = getattr(hashlib, alg, hashlib.sha1())()

    def update(self, string):
        self.hash.update(string)

    def hexdigest(self):
        return self.hash.hexdigest()


class DuplicateFinder:

    def __init__(self, top_directory, max_files_to_check=MAX_FILES, alg=DEFAULT_ALG):
        """
        :param str top_directory: target directory where script will try to find duplicates of files
        :param int max_files_to_check: max number of files that will be stored in dictionary
        :param str alg: selected algorithm to check files
        """
        self.top_directory = top_directory
        self.files = {}  # dict where key is file path and value is hash sum
        self.duplicates = {}  # list of duplicated files
        self.results = OrderedDict()  # dict with check results
        self.max_files_to_check = max_files_to_check  # maximum number of files for check to scale a time of execution
        self.alg = alg  # hashing algorithm
        logger.info(msg='Selected hashing type: {}'.format(self.alg))

        self.f_hashes = None  # list of all calculated hashes
        self.f_sizes = None  # list of all files sizes
        self.total_size = None  # total size of checked files
        self.duplicates_size = None  # total size of duplicated files
        self.start_time = time.time()
        self.end_time = None
        self.degree = UNITS[SIZE_UNIT][0]  # set up degree value for calculate file size
        self.unit = UNITS[SIZE_UNIT][1]  # set up unit value for show file size

        logger.info(msg='Unit degree: {}'.format(self.degree))
        logger.info(msg='Unit value: {}'.format(self.unit))

    def get_files_sizes(self):
        """
        Get list with sizes of all checked files
        """
        self.f_sizes = [int(f_meta["f_size"]) for f_meta in self.files.values() if f_meta["f_size"]]

    def get_total_size(self):
        """
        Get total size of all checked files
        """
        total_size = sum(self.f_sizes)
        self.total_size = round(total_size / (1024 ** self.degree), 2)
        logger.debug(msg='Total size: {} {}'.format(self.total_size, self.unit))

    def get_duplicates_size(self):
        """
        Get total size of duplicated files
        """
        duplicates_size = []
        for f_hash, f_list in self.duplicates.items():
            for f_path in f_list[1:]:  # do not count first file
                duplicates_size.append(self.files.get(f_path).get("f_size", 0))

        self.duplicates_size = sum(duplicates_size)
        self.duplicates_size = round(self.duplicates_size / (1024 ** self.degree), 2)
        logger.debug(msg='Duplicated files size: {} {}'.format(self.duplicates_size, self.unit))

    @staticmethod
    def get_file_size(f_path):
        """
        Get file size
        :param str f_path: path to file
        :return: file size
        """
        try:
            return os.path.getsize(f_path)
        except OSError as e:
            logger.error(msg=e)
            return None

    def get_files(self):
        """
        Find and save in dict all files from target directory
        Key is file path and Value is hash sum of file(None for this step)
        """
        logger.info(msg='Start collecting of files')
        counter = 0

        try:
            for result in os.walk(top=self.top_directory):
                current_dir, included_dirs, included_files = result

                for f in included_files:
                    f_path = os.path.join(current_dir, f)
                    self.files.update({f_path: {"f_hash": None, "f_size": self.get_file_size(f_path)}})
                    counter += 1

                if counter > self.max_files_to_check: break

        except (OSError, PermissionError) as e:
            logger.error(msg=e)

    def get_hash_of_file(self, f_path):
        """
        Open file, calculate hash of file
        :param str f_path: path to file
        :return: hash of file
        """
        f_hash = Hash(alg=self.alg)

        try:
            with open(f_path, 'rb') as f_file:
                for buf in f_file:
                    f_hash.update(buf)
            return f_path, f_hash.hexdigest()

        except (PermissionError, OSError) as e:
            logger.error(msg=e)
            return f_path, None

    def get_hashes(self):
        """
        Open each file from files dict and calculate hash sum
        """
        logger.info(msg='Start calculating hashes')
        self.get_files_sizes()
        files = [f_path for f_path, f_meta in self.files.items() if self.f_sizes.count(f_meta["f_size"]) > 1]

        pool = Pool(processes=PROCESSES)
        results = pool.map(func=self.get_hash_of_file, iterable=files)
        pool.close()
        pool.join()

        for f_path, f_hash in results:
            self.files[f_path]["f_hash"] = f_hash

    def add_duplicate(self, f_hash, f_path):
        """
        Add to duplicate dict new(or another) file path
        :param str f_hash: hash of file
        :param str f_path: path of file
        """
        if self.duplicates.get(f_hash):
            f_list = self.duplicates.get(f_hash)
            f_list.append(f_path)
            logger.debug(msg='Add duplicated file: {}'.format(f_path))

        else:
            logger.debug(msg='Add another duplicated file: {}'.format(f_path))
            self.duplicates.update({f_hash: [f_path]})

    def find(self):
        """
        Find files with equal hashes
        """
        logger.info(msg='Finding duplicates')
        self.f_hashes = [f_meta["f_hash"] for f_meta in self.files.values() if f_meta["f_hash"]]

        for f_path, f_meta in self.files.items():
            if self.f_hashes.count(f_meta["f_hash"]) > 1:
                self.add_duplicate(f_path=f_path, f_hash=f_meta["f_hash"])

        self.end_time = time.time()
        self.get_total_size()
        self.get_duplicates_size()

    def calculate_results(self):
        """
        Aggregate results of check in dict
        """
        duration = round(self.end_time - self.start_time, 2)
        logger.debug(msg='Duration time: {}'.format(duration))

        self.results.update({"Target directory": TARGET_DIR})
        self.results.update({"Files found": self.files.__len__()})
        self.results.update({"Files checked": self.f_hashes.__len__()})
        self.results.update({"Duplicates found": self.duplicates.__len__()})
        self.results.update({"Total size of files": "{} {}".format(self.total_size, self.unit)})
        self.results.update({"Total size of duplicates": "{} {}".format(self.duplicates_size, self.unit)})
        self.results.update({"Total duration": "{} sec".format(duration)})
        self.results.update({"Processes": PROCESSES})
        self.results.update({"Algorithm": self.alg})

    def show_duplicates(self):
        """
        Print duplicate files in cmd
        """
        logger.info(msg='Show duplicates in console')
        for f_hash, f_list in self.duplicates.items():
            print("=" * 100)
            files = "\n".join([f_path for f_path in f_list])
            print(files)
        print("=" * 100)

    def write_results_to_file(self, file=RESULTS_FILE):
        """
        Write results to file for further processing
        :param str file: path to log file
        """
        logger.info(msg='Write results to file: {}'.format(file))

        try:
            log_file = open(file=file, mode="a")
            json.dump(self.results, log_file)
            log_file.write("\n")
            log_file.close()
        except OSError as e:
            logger.error(msg=e)

    def show_results(self):
        """
        Show results of check
        """
        logger.info(msg='Show results in console')
        for key, value in self.results.items():
            print("{}: {}".format(key, value))
            logger.debug(msg="{}: {}".format(key, value))


class Files:

    def __init__(self, top_dir=TARGET_DIR, max_files=MAX_FILES):
        self.top_dir = top_dir
        self.max_files = max_files

    def find(self, top=None, max_files=None):
        """
        Find all files in directory. Limited by max_files
        :param top:
        :param max_files:
        :return:
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
                    files.update({f_path: {"f_size": self.get_file_size(f_path)}})
                    counter += 1

                if counter > max_files: break

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
            return None

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


class Hashes:

    def __init__(self, alg=DEFAULT_ALG):
        self.alg = alg

    def get_hash_of_file(self, f_path, alg=None):
        """
        Open file, calculate hash of file and return it if it exists
        """
        if not alg:
            alg = self.alg
        hasher = getattr(hashlib, alg, hashlib.sha1())()

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
        :param dict hashes:
        :param str f_hash:
        :param str f_path:
        """
        if f_hash in hashes:
            hashes[f_hash]['f_paths'].append(f_path)
            paths = set(hashes[f_hash]['f_paths'])
            paths = list(paths)  # remove duplicated paths just in case
            paths.sort()
            hashes[f_hash]['f_paths'] = paths
        else:
            hashes.update({f_hash: {'f_paths': [f_path]}})

    def calculate_hashes(self, equal_files):
        hashes = {}

        for f_path in equal_files:
            f_hash = self.get_hash_of_file(f_path)
            self.add_hash(hashes=hashes, f_hash=f_hash, f_path=f_path)

        return hashes


class Duplicates:

    def __init__(self, args=None):
        # Store console args
        self.args = args

        # Init main instances
        self.files = {}
        self.equal_files = []
        self.hashes = {}
        self.duplicates = {}
        self.results = OrderedDict()

        # Init time measuring var
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

    def find_all_files(self, top_dir=None, max_files=None):
        """
        Find all files in target directory using Files object.
        Keep passing vars and returning for unit tests
        """
        logger.info(msg='Start scanning the directory: {}'.format(self.args.path if self.args else TARGET_DIR))
        start = time.time()

        if not top_dir or not max_files:
            files = self.files_obj.find()
        else:
            files = self.files_obj.find(top=top_dir, max_files=max_files)

        logger.info(msg='Complete scanning the directory')
        duration = round(time.time() - start, 1)
        self.timing['Scanning time'] = duration

        self.files = deepcopy(files)
        return files

    def check_all_files(self, files=None):
        """
        Check all found files(using Files object) and store all equal files by size.
        Keep passing vars and returning for unit tests
        """
        if not files:
            files = self.files

        logger.info(msg='Start checking found files for equal size')
        start = time.time()

        equal_files = self.files_obj.find_equal_files(files=files)

        logger.info(msg='Complete checking found files')
        duration = round(time.time() - start, 1)
        self.timing['Checking time'] = duration

        self.equal_files = equal_files.copy()
        return equal_files

    def get_files_hashes(self, equal_files=None):
        """
        Get hashes for all found equal files(using Hashes object) and store it.
        Keep passing vars and returning for unit tests
        """
        logger.info(msg='Start calculating hashes')
        start = time.time()

        if not equal_files:
            equal_files = self.equal_files

        hashes = self.hashes_obj.calculate_hashes(equal_files=equal_files)

        logger.info(msg='Complete calculating hashes')
        duration = round(time.time() - start, 1)
        self.timing['Hashing time'] = duration

        self.hashes = deepcopy(hashes)
        return hashes

    def find_duplicates(self, hashes=None):
        logger.info(msg='Start finding equal files by hash')
        start = time.time()

        if not hashes:
            hashes = self.hashes
        duplicates = {}

        for f_hash, paths in hashes.items():

            if len(paths['f_paths'][1:]):
                f_size = self.get_file_size(paths['f_paths'])
                duplicates.update({f_hash: {'f_paths': paths['f_paths'], 'f_size': f_size}})

        logger.info(msg='Complete finding equal files')
        duration = round(time.time() - start, 1)
        self.timing['Finding time'] = duration

        self.duplicates = deepcopy(duplicates)
        return duplicates

    def get_file_size(self, f_paths):
        """
        Try to get file size files dict or directly from OS. Because all files in list have equal size,
        it's fine to size any of them.
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
        Get size of all scanned files in target directory
        """
        if not files:
            files = self.files

        scanned_size = sum([int(f_meta.get('f_size')) for f_meta in files.values() if f_meta.get('f_size')])
        scanned_size = round(scanned_size / (1024 ** self.degree), 2)
        return scanned_size

    def get_hashed_size(self, hashes=None):
        """
        Get size of all hashed files
        """
        if not hashes:
            hashes = self.hashes

        hashed_size = 0
        for h_meta in hashes.values():
            f_size = self.get_file_size(f_paths=h_meta['f_paths'])
            hashed_size += len(h_meta['f_paths']) * f_size

        hashed_size = round(hashed_size / (1024 ** self.degree), 2)
        return hashed_size

    def get_duplicates_size(self, duplicates=None):
        """
        Get size of all duplicated files
        """
        if not duplicates:
            duplicates = self.duplicates

        duplicated_size = 0
        for f_meta in duplicates.values():
            f_paths, f_size = f_meta['f_paths'], f_meta['f_size']

            if f_size:
                duplicated_size += (len(f_paths) - 1) * f_size
            else:
                duplicated_size += (len(f_paths) - 1) * self.get_file_size(f_paths[0])

        duplicated_size = round(duplicated_size / (1024 ** self.degree), 2)
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
        self.results.update({"Total time": "{} sec".format(sum(self.timing.values()))})
        self.results.update({"Algorithm": self.alg})

    def show_results(self):
        """
        Show results in console
        """
        logger.info(msg='Show results in console')
        for key, value in self.results.items():
            print("{}: {}".format(key, value))
            logger.debug(msg="{}: {}".format(key, value))


if __name__ == '__main__':

    # user mode
    if len(sys.argv) > 1:
        duplicates_obj = Duplicates(args=args.parser.parse_args())

    # debug mode
    else:
        duplicates_obj = Duplicates()

    duplicates_obj.find_all_files()
    duplicates_obj.check_all_files()
    duplicates_obj.get_files_hashes()
    duplicates_obj.find_duplicates()
    duplicates_obj.calculate_results()
    duplicates_obj.show_results()
