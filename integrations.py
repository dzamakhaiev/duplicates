import os
import unittest
import duplicates
import file_handler

from test_input import TEST_DIR
from test_input import INTEGRATION_FILES_CHECK
from test_input import INTEGRATION_HASHES_CHECK


class Integration(unittest.TestCase):

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


class IntegrationFiles(Integration):
    """
    Check intercommunication of methods from Files class
    """

    def setUp(self):
        self.files_instance = duplicates.Files()

    def test_files_class(self):
        """
        Method 'find' should return a dict with files and sizes.
        Then method 'find_equal_files' should find equal by size files and return them in list.
        """

        for desc, input_dict, expected in INTEGRATION_FILES_CHECK:
            with self.subTest(msg=desc):

                # Create file structure in current directory for test find method
                old_dir, test_dir = self.create_file_structure(input_dict=input_dict)

                # Check created directory with files
                files = self.files_instance.find(top=test_dir)
                equal_files = self.files_instance.find_equal_files(files)

                # Clean up
                self.delete_file_structure(old_dir, test_dir)
                self.assertEqual(equal_files, expected)


class IntegrationHashes(Integration):
    """
    Check intercommunication of methods from Hashes class and methods from Files class
    """

    def setUp(self):
        self.files_instance = duplicates.Files()
        self.hashes_instance = duplicates.Hashes()

    def test_files_hashes_classes(self):
        """
        Method 'find' should return a dict with files and sizes.
        Then method 'find_equal_files' should find equal by size files and return them in list.
        """

        for desc, input_dict, expected in INTEGRATION_HASHES_CHECK:
            with self.subTest(msg=desc):

                # Create file structure in current directory for test find method
                old_dir, test_dir = self.create_file_structure(input_dict=input_dict)

                # Check created directory with files
                files = self.files_instance.find(top=test_dir)
                equal_files = self.files_instance.find_equal_files(files)

                # Calculate hashes for found files
                hashes = self.hashes_instance.calculate_hashes(equal_files)

                # Clean up
                self.delete_file_structure(old_dir, test_dir)
                self.assertEqual(len(hashes), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
