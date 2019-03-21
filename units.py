import unittest
import duplicates


class UnitFiles(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.equal_dict = {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 123}}
        cls.not_equal_dict = {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 321}}

    def setUp(self):
        self.files_instance = duplicates.Files()

    def test_find_equal_files(self):

        with self.subTest(msg='Check dict with equal files by size'):
            result = self.files_instance.find_equal_files(files=self.equal_dict)
            self.assertTrue(result)

        with self.subTest(msg='Check dict with not equal files by size'):
            result = self.files_instance.find_equal_files(files=self.not_equal_dict)
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
