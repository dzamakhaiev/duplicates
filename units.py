import os
import unittest
import duplicates
import file_handler


from test_input import TEST_DIR
from test_input import TEST_FILE
from test_input import EQUALITY_CHECK
from test_input import SIZE_CHECK
from test_input import DUPLICATES_CHECK
from test_input import FIND_CHECK
from test_input import HASH_CHECK
from test_input import HASHING_CHECK
from test_input import SCAN_SIZE_CHECK
from test_input import HASH_SIZE_CHECK
from test_input import DUPLICATES_SIZE_CHECK


class Unit(unittest.TestCase):

    @staticmethod
    def create_file_structure(input_dict):
        # Create test dir
        file_handler.create_dir(TEST_DIR)
        old_dir = os.getcwd()
        test_dir = os.path.join(old_dir, TEST_DIR)
        os.chdir(test_dir)

        # Create file structure in current directory for test find method
        file_handler.create_file_structure(file_structure=input_dict)
        return old_dir, test_dir

    @staticmethod
    def delete_file_structure(old_dir, test_dir):
        # Clean up
        os.chdir(old_dir)
        file_handler.delete_dir_recursively(test_dir)


class UnitFiles(Unit):

    def setUp(self):
        self.files_instance = duplicates.Files()

    def test_get_files_sizes(self):
        """
        Check get_files_sizes. This method find and collect all file sizes in input dict
        and returns list with integers or empty list.
        """
        for desc, input_dict, expected in SIZE_CHECK:
            with self.subTest(msg=desc):

                result = self.files_instance.get_files_sizes(files=input_dict)
                self.assertEqual(expected, result)

                results = [True if isinstance(size, int) else False for size in result]
                self.assertTrue(all(results))

    def test_find_equal_files(self):
        """
        Check find_equal_files method of Files class. This method checks dict with files {file path: {file size, etc}}
        and returns list with equal files compared by size.
        If no such files - returns empty list.
        """

        for desc, input_dict, expected in EQUALITY_CHECK:
            with self.subTest(msg=desc):

                result = self.files_instance.find_equal_files(files=input_dict)
                if expected:
                    self.assertTrue(result)
                else:
                    self.assertEqual(expected, result)

    def test_find(self):
        """
        Check find method of Files class. This method walks recursively in directory and
        collects all found files in dict. Returns dict with files and sizes.
        """
        for desc, input_dict, expected in FIND_CHECK:
            with self.subTest(msg=desc):

                # Create file structure in current directory for test find method
                old_dir, test_dir = self.create_file_structure(input_dict=input_dict)
                result = self.files_instance.find(top=test_dir)

                # Clean up
                self.delete_file_structure(old_dir, test_dir)

                self.assertEqual(result, expected)


class UnitHashes(Unit):

    def setUp(self):
        self.hashes_instance = duplicates.Hashes()

    def test_get_hash(self):
        """
        Check get_hash_of_file in Hashes class. This method get hash of file or return None in case of error.
        Method could use various hashing protocols.
        """
        filename = 'file_for_hashing.bin'

        for desc, alg in HASHING_CHECK:
            with self.subTest(msg=desc):
                file_handler.create_file(filename)
                result = self.hashes_instance.get_hash_of_file(f_path=filename)
                file_handler.delete_file(filename)
                self.assertTrue(result, msg='Hash should not be None')

        # Try to get hash of deleted file
        result = self.hashes_instance.get_hash_of_file(f_path=filename)
        self.assertFalse(result, msg='Hash should be None')

    def test_add_hash(self):
        """
        Check add_hash. This method update hashes dict with new hashes and paths. Returns nothing.
        If dict already has hash, add new file path linked to this hash.
        """
        for desc, input_dict, f_hash, f_path, expected in HASH_CHECK:
            with self.subTest(msg=desc):

                self.hashes_instance.add_hash(hashes=input_dict, f_hash=f_hash, f_path=f_path)
                self.assertEqual(expected, input_dict)

    def test_calculate_hashes(self):
        """
        Check calculate_hashes method in Hashes class.
        It calculates hashes for list of files and returns their hashes.
        """

        with self.subTest(msg='Test identical files'):
            number_of_copies = 4

            # create new file and copy it n times
            file_handler.create_file(TEST_FILE)
            copies = file_handler.copy_file(TEST_FILE, number_of_copies)
            copies.append(TEST_FILE)

            hashes = self.hashes_instance.calculate_hashes(equal_files=copies)
            file_handler.delete_list_of_files(copies)
            exp_hashes = 1
            self.assertEqual(len(hashes), exp_hashes, msg='Should be only one hash for equal files')

        with self.subTest(msg='Test diff files'):
            number_of_files = 5

            # create new files with diff size
            files = file_handler.create_files(filename=TEST_FILE, n=number_of_files, random_size=True)

            hashes = self.hashes_instance.calculate_hashes(equal_files=files)
            file_handler.delete_list_of_files(files)

            self.assertEqual(len(hashes), number_of_files, msg='Number of hashes should be equal to number of files')

        # test empty list
        hashes = self.hashes_instance.calculate_hashes(equal_files=[])
        self.assertEqual(len(hashes), len([]), msg='Test empty list of hashes and files')


class UnitDuplicates(Unit):

    def setUp(self):
        self.duplicates_instance = duplicates.Duplicates()

    def test_find_all_files(self):
        """
        Check find_all_files method in Duplicates class. This method try to find all files in
        top directory and collect in dictionary. Dict limited by max_files var.
        """
        # create test top dir and change current dir
        file_handler.create_dir(TEST_DIR)
        old_dir = os.getcwd()
        top_dir = os.path.join(old_dir, TEST_DIR)
        os.chdir(top_dir)

        # create test files in current dir
        max_files = 5
        file_handler.create_files(filename=TEST_FILE, n=max_files*2)
        result = self.duplicates_instance.find_all_files(top_dir=top_dir, max_files=max_files)
        self.delete_file_structure(old_dir=old_dir, test_dir=top_dir)

        # check len of dict
        self.assertEqual(len(result), max_files)

    def test_check_all_files(self):
        """
        Check check_all_files method in Duplicates class. This method check dict with files
        to find equal files by size.
        """
        for desc, input_dict, expected in EQUALITY_CHECK:
            with self.subTest(msg=desc):
                results = self.duplicates_instance.check_all_files(files=input_dict)

                if isinstance(expected, bool):
                    exp_len = 2
                    self.assertEqual(len(results), exp_len)
                else:
                    self.assertEqual(len(results), len(expected))

    def test_get_files_hashes(self):
        """
        Check get_files_hashes method in Duplicates class. This method delegates
        calculating hashes task to Hashes class.
        """
        number_of_files = 5

        # create new files with diff size
        files = file_handler.create_files(filename=TEST_FILE, n=number_of_files, random_size=True)

        hashes = self.duplicates_instance.get_files_hashes(equal_files=files)
        file_handler.delete_list_of_files(files)

        self.assertEqual(len(hashes), number_of_files, msg='Number of hashes should be equal to number of files')

    def test_find_duplicates(self):
        """
        Check find_duplicates method. This method find duplicated files by its hashes.
        Input: dict {hash: {paths:[....]}}. If hash has more than one linked file path
        that hash adding to duplicates dict. If input dict has no duplicates, method returns empty dict.
        """

        for desc, input_dict, expected in DUPLICATES_CHECK:
            with self.subTest(msg=desc):

                result = self.duplicates_instance.find_duplicates(hashes=input_dict)
                self.assertEqual(expected, result)

    def test_get_file_size(self):
        """
        Check get_file_size method in Duplicates class. This method try to get file size from
        internal dict 'files', or directly from drive, or return 0 bytes.
        """
        with self.subTest(msg='Using data from internal dict in self'):
            # add in self.files test file
            exp_size = 1000
            self.duplicates_instance.files.update({TEST_FILE: {'f_size': exp_size}})
            size = self.duplicates_instance.get_file_size([TEST_FILE])
            self.duplicates_instance.files.pop(TEST_FILE)
            self.assertEqual(size, exp_size)

        with self.subTest(msg='Using data directly from drive'):
            # add in self.files test file
            exp_size = 2000
            file_handler.create_file(filename=TEST_FILE, n_bytes=exp_size)
            size = self.duplicates_instance.get_file_size([TEST_FILE])
            file_handler.delete_file(TEST_FILE)
            self.assertEqual(size, exp_size)

        exp_size = 0
        size = self.duplicates_instance.get_file_size([TEST_FILE])
        self.assertEqual(size, exp_size)

    def test_get_scanned_size(self):
        """
        Check get_scanned_size method from Duplicates class. This method calculates total size of all scanned files
        and returns value in kb, mb, gb, tb units.
        """
        for desc, input_dict, degree, exp_size in SCAN_SIZE_CHECK:
            with self.subTest(msg=desc):
                self.duplicates_instance.degree = degree
                results = self.duplicates_instance.get_scanned_size(files=input_dict)
                self.assertEqual(results, exp_size)

    def test_get_hashed_size(self):
        """
        Check get_hashed_size method from Duplicates class. This method calculates total size of all hashed files
        and returns value in kb, mb, gb, tb units. Also this method could get file size from 'files' dict.
        """
        for desc, files_dict, hashes_dict, degree, exp_size in HASH_SIZE_CHECK:
            with self.subTest(msg=desc):
                self.duplicates_instance.degree = degree
                self.duplicates_instance.files = files_dict
                results = self.duplicates_instance.get_hashed_size(hashes=hashes_dict)
                self.assertEqual(results, exp_size)

    def test_get_duplicates_size(self):
        """
        Check get_duplicates_size method from Duplicates class. This method calculates total size
        of all duplicated files and returns value in kb, mb, gb, tb units.
        Also this method could get file size from 'files' dict or from 'duplicates' dict.
        """
        for desc, files_dict, duplicates_dict, degree, exp_size in DUPLICATES_SIZE_CHECK:
            with self.subTest(msg=desc):
                self.duplicates_instance.degree = degree
                self.duplicates_instance.files = files_dict
                results = self.duplicates_instance.get_duplicates_size(duplicates=duplicates_dict)
                self.assertEqual(results, exp_size)


if __name__ == '__main__':
    unittest.main(verbosity=2)
