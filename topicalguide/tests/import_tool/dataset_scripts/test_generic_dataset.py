from __future__ import print_function

import os

from import_tool.dataset_scripts.generic_dataset import GenericDataset, GenericDocument


def test_generic_document_methods():
    this_dir = os.path.dirname(__file__)
    root_dataset_dir = os.path.abspath(os.path.join(this_dir, 'test_resources/'))
    
    test1_file = os.path.join(root_dataset_dir, 'documents/test1.txt')
    doc = GenericDocument(root_dataset_dir, test1_file)
    
    assert doc.get_identifier() == 'documents_test1.txt'
    assert doc.get_content() == 'content\n\ncontent'
    
    actual_metadata = {}
    for i in range(1,4):
        actual_metadata['meta%d'%i] = 'value1-%d'%i
    
    for key in doc.get_metadata():
        assert key in actual_metadata
        assert doc.get_metadata()[key] == actual_metadata[key]

def test_generic_dataset_methods():
    this_dir = os.path.dirname(__file__)
    root_dataset_dir = os.path.abspath(os.path.join(this_dir, 'test_resources/'))
    dataset = GenericDataset(root_dataset_dir)
    
    
    
    assert dataset.get_identifier() == 'test_with_spaces_and_semicolon'
    assert dataset.get_readable_name() == 'Test With Spaces: And Semicolon'
    assert dataset.get_description() == 'Testing'
    
    actual_dataset_meta = {'creator': 'Me1', 'source': 'Me2'}
    meta = dataset.get_metadata()
    for t in meta:
        assert t in actual_dataset_meta
        assert meta[t] == actual_dataset_meta[t]
    assert len(meta) == len(actual_dataset_meta)
    
    doc_names = ['test1.txt', 'test2.txt', 'test_directory_test3.txt', 'test_directory_test_dir2_test4.txt']
    doc_count = 0
    for doc in dataset:
        doc_count += 1
        assert doc.get_identifier() in doc_names
    assert len(doc_names) == doc_count
