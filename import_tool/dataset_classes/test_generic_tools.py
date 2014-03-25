from __future__ import print_function

import os

from generic_tools import GenericTools


def test_metadata_to_dict():
    meta = """YEAR: 1983
MONTH: Nov.
SPEAKER: Marvin J. Ashton
CALLING: Of the Quorum of the Twelve Apostles
TOPIC: commitment"""
    meta_dict = GenericTools.metadata_to_dict(meta)
    
    actual_meta_dict = {'year': '1983', 'month': 'Nov.', 'speaker': 'Marvin J. Ashton',
                        'topic': 'commitment'}
    
    for key in actual_meta_dict:
        assert key in meta_dict
        assert meta_dict[key] == actual_meta_dict[key]


def test_get_all_files_from_directory():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    directory = 'test_resources/documents'
    path = os.path.join(root_dir, directory)
    
    files = GenericTools.get_all_files_from_directory(path)
    assert os.path.join(path, 'test1.txt') in files
    assert os.path.join(path, 'test2.txt') in files
    
    path2 = os.path.join(path, 'test_directory')
    files2 = GenericTools.get_all_files_from_directory(path, True)
    print(files2)
    assert os.path.join(path, 'test1.txt') in files2
    assert os.path.join(path, 'test2.txt') in files2
    assert os.path.join(path2, 'test3.txt') in files2
    assert os.path.join(path2, 'test_dir2/test4.txt') in files2
    
