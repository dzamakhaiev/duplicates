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