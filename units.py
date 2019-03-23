import unittest
import duplicates

TEST_DICTS = [
    ('Test dict with equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 123}}, True),
    ('Test dict with not equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 321}}, []),
    ('Test dict with empty file size', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': None}}, []),
    ('Test dict with empty meta dict', {'test_path_0': {'f_size': 123}, 'test_path_1': {}}, []),
    ('Test empty dict', {}, []),
]


class UnitFiles(unittest.TestCase):

    def setUp(self):
        self.files_instance = duplicates.Files()

    def test_find_equal_files(self):
        """
        Check find_equal_files method. This method checks dict with files {file path: {file size, etc}}
        and returns list with equal files compared by size.
        If no such files - returns empty list.
        """

        for desc, input_dict, expected in TEST_DICTS:
            with self.subTest(msg=desc):

                result = self.files_instance.find_equal_files(files=input_dict)
                if expected:
                    self.assertTrue(result)
                else:
                    self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
