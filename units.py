import unittest
import duplicates

EQUALITY_CHECK = [
    ('Test dict with equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 123}}, True),
    ('Test dict with not equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 321}}, []),
    ('Test dict with empty file size', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': None}}, []),
    ('Test dict with empty meta dict', {'test_path_0': {'f_size': 123}, 'test_path_1': {}}, []),
    ('Test empty dict', {}, [])]

SIZE_CHECK = [
    ('Test dict with both sizes', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 456}}, [123, 456]),
    ('Test dict with one size only ', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': None}}, [123]),
    ('Test dict with no sizes', {'test_path_0': {'f_size': None}, 'test_path_1': {'f_size': None}}, []),
    ('Test dict with empty meta dict for one file', {'test_path_0': {'f_size': 123}, 'test_path_1': {}}, [123]),
    ('Test empty dict', {}, [])]

DUPLICATES_CHECK = [
    ('Test dict with hash that has multiple files',
     {'hash0': {'f_paths': ['path0', 'path1']}, 'hash1': {'f_paths': ['path2']}},
     {'hash0': {'f_paths': ['path0', 'path1'], 'f_size': 0}}),
    ('Test dict with unique hashes and files',
     {'hash0': {'f_paths': ['path0']}, 'hash1': {'f_paths': ['path1']}}, {}),
    ('Test empty dict', {}, {}),
]

HASH_CHECK = [
    ('Test adding hash firs time', {}, 'hash0', 'path0', {'hash0': {'f_paths': ['path0']}}),
    ('Test adding hash second time', {'hash0': {'f_paths': ['path0']}}, 'hash0', 'path1', {'hash0': {'f_paths': ['path0', 'path1']}}),
    ('Test adding duplicated path', {'hash0': {'f_paths': ['path0']}}, 'hash0', 'path0', {'hash0': {'f_paths': ['path0']}})
]


class UnitFiles(unittest.TestCase):

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
        Check find_equal_files method. This method checks dict with files {file path: {file size, etc}}
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


class UnitHashes(unittest.TestCase):

    def setUp(self):
        self.hashes_instance = duplicates.Hashes()

    def test_add_hash(self):
        """
        Check add_hash. This method update hashes dict with new hashes and paths. Returns nothing.
        If dict already has hash, add new file path linked to this hash.
        """
        for desc, input_dict, f_hash, f_path, expected in HASH_CHECK:
            with self.subTest(msg=desc):

                self.hashes_instance.add_hash(hashes=input_dict, f_hash=f_hash, f_path=f_path)
                self.assertEqual(expected, input_dict)


class UnitDuplicates(unittest.TestCase):

    def setUp(self):
        self.duplicates_instance = duplicates.Duplicates()

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
