import os


TEST_DIR = r'test_dir'
TEST_FILE = r'test.bin'


# test description, input dict, expected result
EQUALITY_CHECK = [
    ('Test dict with equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 123}}, True),
    ('Test dict with not equal files', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 321}}, []),
    ('Test dict with empty file size', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': None}}, []),
    ('Test dict with empty meta dict', {'test_path_0': {'f_size': 123}, 'test_path_1': {}}, []),
    ('Test empty dict', {}, [])
]

# test description, input dict, expected result
SIZE_CHECK = [
    ('Test dict with both sizes', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': 456}}, [123, 456]),
    ('Test dict with one size only ', {'test_path_0': {'f_size': 123}, 'test_path_1': {'f_size': None}}, [123]),
    ('Test dict with no sizes', {'test_path_0': {'f_size': None}, 'test_path_1': {'f_size': None}}, []),
    ('Test dict with empty meta dict for one file', {'test_path_0': {'f_size': 123}, 'test_path_1': {}}, [123]),
    ('Test empty dict', {}, [])]

# test description, input dict, expected result
DUPLICATES_CHECK = [
    ('Test dict with hash that has multiple files',
     {'hash0': {'f_paths': ['path0', 'path1']}, 'hash1': {'f_paths': ['path2']}},
     {'hash0': {'f_paths': ['path0', 'path1'], 'f_size': 0}}),
    ('Test dict with unique hashes and files',
     {'hash0': {'f_paths': ['path0']}, 'hash1': {'f_paths': ['path1']}}, {}),
    ('Test empty dict', {}, {}),
]

# test description, input dict, expected result
HASH_CHECK = [
    ('Test adding hash firs time', {}, 'hash0', 'path0', {'hash0': {'f_paths': ['path0']}}),
    ('Test adding hash second time', {'hash0': {'f_paths': ['path0']}}, 'hash0', 'path1', {'hash0': {'f_paths': ['path0', 'path1']}}),
    ('Test adding duplicated path', {'hash0': {'f_paths': ['path0']}}, 'hash0', 'path0', {'hash0': {'f_paths': ['path0']}})
]

# test description, input dict with file structure, expected result in dict
current_dir = os.getcwd()
test_dir = os.path.join(current_dir, TEST_DIR)
FIND_CHECK = [
    ('Test dict with diff files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 10000, 'file2.txt': 100000}},
     {os.path.join(test_dir, 'dir0', 'file0.txt'): {'f_size': 1000},
      os.path.join(test_dir, 'dir0', 'file1.txt'): {'f_size': 10000},
      os.path.join(test_dir, 'dir0', 'file2.txt'): {'f_size': 100000}}),
    ('Test dict with equal files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 1000, 'file2.txt': 1000}},
     {os.path.join(test_dir, 'dir0', 'file0.txt'): {'f_size': 1000},
      os.path.join(test_dir, 'dir0', 'file1.txt'): {'f_size': 1000},
      os.path.join(test_dir, 'dir0', 'file2.txt'): {'f_size': 1000}})
]

# test description, hashing algorithm
HASHING_CHECK = [
    ('Check that method will return hash of file', 'MD5'),
    ('Check that method will return hash of file even if hash type is incorrect', 'BFG')
]

# test description, input dict, degree, expected result
SCAN_SIZE_CHECK = [
    ('Check calculating total file size in KB', {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 4096}}, 1, 6),
    ('Check calculating total file size in MB', {'test1.txt': {'f_size': 1500000}, 'test2.txt': {'f_size': 1120000}}, 2, 2.5),
    ('Check calculating total file size in GB', {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 4096}}, 3, 0),
    ('Check calculating total file size in TB', {'test1.txt': {'f_size': 5000000000}, 'test2.txt': {'f_size': 4500000000}}, 4, 0.01),
]

# test description, files dict, hashes dict, degree, expected result
HASH_SIZE_CHECK = [
    ('Check calculating total file size in KB',
     {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 2048}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 1, 4),
    ('Check calculating total file size in MB',
     {'test1.txt': {'f_size': 1500000}, 'test2.txt': {'f_size': 1500000}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 2, 2.86),
    ('Check calculating total file size in GB',
     {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 2048}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 3, 0),
    ('Check calculating total file size in TB',
     {'test1.txt': {'f_size': 25500000000}, 'test2.txt': {'f_size': 25500000000}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 4, 0.05),
]

# test description, files dict, hashes dict, degree, expected result
DUPLICATES_SIZE_CHECK = [
    ('Check calculating total file size in KB',
     {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 2048}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt'], 'f_size': 2048}}, 1, 2),
    ('Check calculating total file size in MB',
     {'test1.txt': {'f_size': 1500000}, 'test2.txt': {'f_size': 1500000}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 2, 1.43),
    ('Check calculating total file size in GB',
     {'test1.txt': {'f_size': 2048}, 'test2.txt': {'f_size': 2048}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt'], 'f_size': 2048}}, 3, 0),
    ('Check calculating total file size in TB',
     {'test1.txt': {'f_size': 22000000000}, 'test2.txt': {'f_size': 22000000000}}, {'hash1': {'f_paths': ['test1.txt', 'test2.txt']}}, 4, 0.02),
]

# test description, input dict with file structure, expected result in list
INTEGRATION_FILES_CHECK = [
    ('Test dict with diff files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 10000, 'file2.txt': 100000}}, []),
    ('Test dict with equal files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 1000, 'file2.txt': 1000}},
     [os.path.join(test_dir, 'dir0', 'file0.txt'),
      os.path.join(test_dir, 'dir0', 'file1.txt'),
      os.path.join(test_dir, 'dir0', 'file2.txt')])
]

# test description, input dict with file structure, expected len
INTEGRATION_HASHES_CHECK = [
    ('Test dict with diff files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 10000, 'file2.txt': 100000}}, 0),
    ('Test dict with equal files by size', {'dir0': {'file0.txt': 1000, 'file1.txt': 1000, 'file2.txt': 1000}}, 1)
]
