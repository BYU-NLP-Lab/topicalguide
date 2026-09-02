
import os

from import_tool.dataset.interfaces.generic_dataset import GenericDataset, GenericDocument


def root_dataset_dir():
    this_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(this_dir, 'test_resources/'))


def documents_dir():
    return os.path.join(root_dataset_dir(), 'documents')


def test_generic_document_methods():
    test1_file = os.path.join(documents_dir(), 'test1.txt')
    doc = GenericDocument(documents_dir(), test1_file)

    assert doc.name == 'test1.txt'
    assert doc.content == 'content\n\ncontent'
    assert doc.source is None

    actual_metadata = {}
    for i in range(1, 4):
        actual_metadata['meta%d' % i] = 'value1-%d' % i

    assert doc.metadata == actual_metadata


def test_generic_document_name_is_relative_to_root():
    """Nested documents get a unique name by flattening their relative path."""
    nested = os.path.join(documents_dir(), 'test_directory', 'test_dir2', 'test4.txt')
    doc = GenericDocument(documents_dir(), nested)

    assert doc.name == 'test_directory_test_dir2_test4.txt'


def test_generic_document_filters_are_applied_to_content():
    test1_file = os.path.join(documents_dir(), 'test1.txt')
    doc = GenericDocument(documents_dir(), test1_file)
    doc.set_filters([lambda text: text.upper()])

    assert doc.content == 'CONTENT\n\nCONTENT'


def test_generic_dataset_methods():
    dataset = GenericDataset(root_dataset_dir())

    assert dataset.name == 'test_with_spaces'

    actual_dataset_meta = {'readable_name': 'Test With Spaces',
                           'description': 'Testing',
                           'creator': 'Me1',
                           'source': 'Me2'}
    assert dataset.metadata == actual_dataset_meta

    doc_names = ['test1.txt', 'test2.txt', 'test_directory_test3.txt',
                 'test_directory_test_dir2_test4.txt']
    assert len(dataset) == len(doc_names)

    doc_count = 0
    for doc in dataset:
        doc_count += 1
        assert doc.name in doc_names
    assert len(doc_names) == doc_count


def test_generic_dataset_collects_metadata_types():
    dataset = GenericDataset(root_dataset_dir())

    assert dataset.metadata_types == {'readable_name': 'text',
                                      'description': 'text',
                                      'creator': 'text',
                                      'source': 'text'}
    assert dataset.document_metadata_types == {'meta1': 'text',
                                               'meta2': 'text',
                                               'meta3': 'text'}


def test_generic_dataset_non_recursive_skips_subdirectories():
    dataset = GenericDataset(root_dataset_dir(), is_recursive=False)

    assert sorted(doc.name for doc in dataset) == ['test1.txt', 'test2.txt']


def test_generic_dataset_name_strips_punctuation(tmp_path):
    """Punctuation is dropped from readable_name and spaces become underscores."""
    (tmp_path / 'dataset_metadata.txt').write_text(
        'readable_name: Test With Spaces: And Semicolon\ndescription: Testing\n')
    documents = tmp_path / 'documents'
    documents.mkdir()
    (documents / 'test1.txt').write_text('meta1: value1-1\n\ncontent')

    dataset = GenericDataset(str(tmp_path))

    assert dataset.metadata['readable_name'] == 'Test With Spaces: And Semicolon'
    assert dataset.name == 'test_with_spaces_and_semicolon'
