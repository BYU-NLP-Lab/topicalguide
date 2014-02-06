from generic_dataset import GenericDataset, GenericDocumentIterator, GenericDocument




def test_document():
    doc = GenericDocument('test_resources/test1.txt', False)
    
    assert doc.get_name() == 'test1.txt'
    assert doc.get_content() == 'content'
    
    metadata = doc.get_metadata()
    test1_metadata = {'test1': 'value1', 'test2': 'value2'}
    for key in metadata:
        assert key in test1_metadata
        assert metadata[key] == test1_metadata[key]
