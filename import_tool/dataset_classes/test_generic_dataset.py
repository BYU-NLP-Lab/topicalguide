import os
from generic_dataset import GenericDataset, GenericDocumentIterator, GenericDocument


def test_generic_document_methods():
    root_dataset_dir = os.path.abspath('test_resources/')
    test1_file = os.path.join(root_dataset_dir, 'documents/test1.txt')
    doc = GenericDocument(root_dataset_dir, test1_file, False)
    
    assert doc.get_name() == 'documents_test1.txt'
    assert doc.get_content() == 'content\n\ncontent'
    assert not doc.has_subdocuments()
    
    actual_metadata = {}
    for i in range(1,4):
        actual_metadata['meta%d'%i] = 'value1-%d'%i
    
    for key in doc.get_metadata():
        assert key in actual_metadata
        assert doc.get_metadata()[key] == actual_metadata[key]
    
def test_generic_dataset_methods():
    pass
