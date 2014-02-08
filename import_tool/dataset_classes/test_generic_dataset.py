from __future__ import print_function

import os

from generic_dataset import GenericDataset, GenericDocument


def test_generic_document_methods():
    root_dataset_dir = os.path.abspath('test_resources/')
    test1_file = os.path.join(root_dataset_dir, 'documents/test1.txt')
    doc = GenericDocument(root_dataset_dir, test1_file)
    doc.set_has_subdocuments(False)
    
    assert doc.get_name() == 'documents_test1.txt'
    assert doc.get_content() == 'content\n\ncontent'
    assert not doc.has_subdocuments()
    
    actual_metadata = {}
    for i in range(1,4):
        actual_metadata['meta%d'%i] = 'value1-%d'%i
    
    for key in doc.get_metadata():
        assert key in actual_metadata
        assert doc.get_metadata()[key] == actual_metadata[key]

def test_generic_subdocument_methods():
    root_dataset_dir = os.path.abspath('test_resources/')
    test2_file = os.path.join(root_dataset_dir, 'documents/test1.txt')
    doc = GenericDocument(root_dataset_dir, test2_file)
    doc.set_has_subdocuments(True)
    
    assert doc.has_subdocuments()
    for sub_doc in doc:
        assert sub_doc.get_content() == 'content'
        assert not sub_doc.has_subdocuments()

def test_generic_dataset_methods():
    root_dataset_dir = os.path.abspath('test_resources/')
    dataset = GenericDataset(root_dataset_dir)
    
    assert dataset.get_dataset_identifier() == 'test_with_spaces'
    
    actual_dataset_types = {'readable_name': 'text', 'description': 'text', 'creator': 'text', 'source': 'text'}
    dataset_types = dataset.get_dataset_metadata_types()
    for t in dataset_types:
        assert t in actual_dataset_types
        assert dataset_types[t] == actual_dataset_types[t]
    assert len(dataset_types) == len(actual_dataset_types)
    
    actual_dataset_meta = {'readable_name': 'Test With Spaces', 'description': 'Testing', 'creator': 'Me1', 'source': 'Me2'}
    meta = dataset.get_dataset_metadata()
    for t in meta:
        assert t in actual_dataset_meta
        assert meta[t] == actual_dataset_meta[t]
    assert len(meta) == len(actual_dataset_meta)
    
    actual_types = {'meta1': 'text', 'meta2': 'text', 'meta3': 'text'}
    types = dataset.get_document_metadata_types()
    for t in types:
        assert t in actual_types
        assert types[t] == actual_types[t]
    assert len(types) == len(actual_types)
    
    doc_names = ['test1.txt', 'test2.txt', 'test_directory_test3.txt']
    doc_count = 0
    for doc in dataset:
        doc_count += 1
        assert doc.get_name() in doc_names
        assert not doc.has_subdocuments()
    assert len(doc_names) == doc_count
