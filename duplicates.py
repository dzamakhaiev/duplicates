#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import time
import json
import logging
from multiprocessing import Pool, freeze_support
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
        self.files = {}
        self.file_sizes = 0

    def find(self, top=None, max_files=None):
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
                    files.update({f_path: {"f_hash": None, "f_size": self.get_file_size(f_path)}})
                    counter += 1

                if counter > max_files: break

        except (OSError, PermissionError) as e:
            logger.error(msg=e)

        self.files = deepcopy(files)  # save dict in self for further use and protect from possible changes
        return files

    def find_equal_files(self, files=None):
        """
        Get list of files with equal size
        """
        if not files:
            files = self.files

        equal_files = []
        file_sizes = self.get_files_sizes(files)

        for f_path, f_meta in files.items():
            if f_meta and f_meta.get('f_size') and file_sizes.count(f_meta['f_size']) > 1:
                equal_files.append(f_path)

        return equal_files

    @staticmethod
    def get_file_size(f_path):
        try:
            return os.path.getsize(f_path)
        except OSError as e:
            logger.error(msg=e)
            return None

    def get_files_sizes(self, files):
        """
        Get list with sizes of all checked files
        """
        if not files:
            files = self.files

        file_sizes = []
        for f_meta in files.values():
            if f_meta and f_meta.get("f_size"):
                file_sizes.append(int(f_meta["f_size"]))

        self.file_sizes = deepcopy(file_sizes)

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
        if hash in hashes:
            hashes[f_hash]['f_paths'].append(f_path)
        else:
            hashes.update({f_hash: {'f_paths': [f_path]}})

    def calculate_hashes(self, equal_files):
        hashes = {}
        for f_path in equal_files:
            f_hash = self.get_hash_of_file(f_path)
            self.add_hash(hashes=hashes, f_hash=f_hash, f_path=f_path)

        return hashes


if __name__ == '__main__':
    freeze_support()

    finder = DuplicateFinder(top_directory=TARGET_DIR)
    finder.get_files()
    finder.get_hashes()
    finder.find()
    finder.show_duplicates()
    finder.calculate_results()
    finder.show_results()
    finder.write_results_to_file()

    # debug
    files = Files(top_dir=TARGET_DIR)
    f = files.find()
    print(len(f))
    e = files.find_equal_files(f)
    print(len(e))
