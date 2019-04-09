import os
import unittest
import duplicates
import file_handler

from test_input import EQUALITY_CHECK
from test_input import SIZE_CHECK
from test_input import DUPLICATES_CHECK
from test_input import FIND_CHECK
from test_input import TEST_DIR
from test_input import HASH_CHECK
from test_input import HASHING_CHECK


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
        test_file = 'test.bin'

        with self.subTest(msg='Test identical files'):
            number_of_copies = 4

            # create new file and copy it n times
            file_handler.create_file(test_file)
            copies = file_handler.copy_file(test_file, number_of_copies)
            copies.append(test_file)

            hashes = self.hashes_instance.calculate_hashes(equal_files=copies)
            file_handler.delete_list_of_files(copies)
            exp_hashes = 1
            self.assertEqual(len(hashes), exp_hashes, msg='Should be only one hash for equal files')

        with self.subTest(msg='Test diff files'):
            number_of_files = 5

            # create new files with diff size
            files = file_handler.create_files(filename=test_file, n=number_of_files, random_size=True)

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
        file_handler.create_files(filename='test.bin', n=max_files*2)
        result = self.duplicates_instance.find_all_files(top_dir=top_dir, max_files=max_files)
        self.delete_file_structure(old_dir=old_dir, test_dir=top_dir)

        # check len of dict
        self.assertEqual(len(result), max_files)

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
