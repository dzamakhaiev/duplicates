#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib
import time
import json
from multiprocessing import Pool, freeze_support
from collections import OrderedDict

TARGET_DIR = r"C:\Program Files (x86)\Steam"
BLOCK_SIZE = 65536
MAX_FILES = 10000
PROCESSES = 2
SIZE_UNIT = "GB"
LOG_FILE = "duplicates.txt"
DEFAULT_ALG = "sha1"


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
        """
        self.top_directory = top_directory
        self.files = {}  # dict where key is file path and value is hash sum
        self.duplicates = {}  # list of duplicated files
        self.results = OrderedDict()  # dict with check results
        self.max_files_to_check = max_files_to_check  # maximum number of files for check to scale a time of execution
        self.alg = alg  # hashing algorithm

        self.f_hashes = None  # list of all calculated hashes
        self.f_sizes = None  # list of all files sizes
        self.total_size = None  # total size of checked files
        self.duplicates_size = None  # total size of duplicated files
        self.start_time = time.time()
        self.end_time = None

        if SIZE_UNIT == "MB":
            self.degree = 2
            self.unit = "megabytes"
        elif SIZE_UNIT == "GB":
            self.degree = 3
            self.unit = "gigabytes"
        elif SIZE_UNIT == "TB":
            self.degree = 4
            self.unit = "terabytes"
        else:
            self.degree = 2
            self.unit = "megabytes"

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

    @staticmethod
    def get_file_size(f_path):
        """
        Get file size
        :param str f_path: path to file
        :return: file size
        """
        try:
            return os.path.getsize(f_path)
        except OSError:
            return None

    def get_files(self):
        """
        Find and save in dict all files from target directory
        Key is file path and Value is hash sum of file(None for this step)
        """
        counter = 0

        for result in os.walk(top=self.top_directory):
            current_dir, included_dirs, included_files = result

            for f in included_files:
                f_path = os.path.join(current_dir, f)
                self.files.update({f_path: {"f_hash": None, "f_size": self.get_file_size(f_path)}})
                counter += 1

            if counter > self.max_files_to_check: break

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

        except (PermissionError, OSError):
            return f_path, None

    def get_hashes(self):
        """
        Open each file from files dict and calculate hash sum
        """
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
        else:
            self.duplicates.update({f_hash: [f_path]})

    def find(self):
        """
        Find files with equal hashes
        """
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
        for f_hash, f_list in self.duplicates.items():
            print("=" * 100)
            files = "\n".join([f_path for f_path in f_list])
            print(files)
        print("=" * 100)

    def write_results_to_file(self, file=LOG_FILE):
        """
        Write results to file for further processing
        :param str file: path to log file
        """
        log_file = open(file=file, mode="a")
        json.dump(self.results, log_file)
        log_file.write("\n")
        log_file.close()

    def show_results(self):
        """
        Measure duration of check
        """
        for key, value in self.results.items():
            print("{}: {}".format(key, value))


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
