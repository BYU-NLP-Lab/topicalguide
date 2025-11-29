
import os

from import_tool import basic_tools


def test_metadata_to_dict():
    meta = """KEY WITH Spaces: Value with: Semi-colon
YEAR: 1983
MONTH: Nov.
SPEAKER: Marvin J. Ashton
CALLING: Of the Quorum of the Twelve Apostles
TOPIC: commitment"""
    meta_dict = basic_tools.metadata_to_dict(meta)
    
    actual_meta_dict = {'key_with_spaces': 'Value with: Semi-colon', 
                        'year': '1983', 
                        'month': 'Nov.', 
                        'speaker': 'Marvin J. Ashton',
                        'topic': 'commitment'}
    
    for key in actual_meta_dict:
        assert key in meta_dict
        assert meta_dict[key] == actual_meta_dict[key]


def test_get_all_files_from_directory():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    directory = 'test_resources/documents'
    path = os.path.join(root_dir, directory)
    
    files = basic_tools.get_all_files_from_directory(path)
    assert os.path.join(path, 'test1.txt') in files
    assert os.path.join(path, 'test2.txt') in files
    
    path2 = os.path.join(path, 'test_directory')
    files2 = basic_tools.get_all_files_from_directory(path, True)
    print(files2)
    assert os.path.join(path, 'test1.txt') in files2
    assert os.path.join(path, 'test2.txt') in files2
    assert os.path.join(path2, 'test3.txt') in files2
    assert os.path.join(path2, 'test_dir2/test4.txt') in files2

def test_create_subdocuments():
    doc_name = 'doc'
    doc_content = 'a'*1000 + '\n' + 'b'*1000
    results = basic_tools.create_subdocuments(doc_name, doc_content)
    name_set = set()
    for result in results:
        name_set.add(result[0])
    assert len(name_set) == 2
    assert results[0][0] == 'doc_subdoc0'
    assert results[0][1] == 'a'*1000
    assert results[1][0] == 'doc_subdoc1'
    assert results[1][1] == 'b'*1000
    doc_content = ''
    results = basic_tools.create_subdocuments(doc_name, doc_content)
    assert results[0][1] == ''
    doc_content = 'a'*999 + '\n'
    results = basic_tools.create_subdocuments(doc_name, doc_content)
    assert results[0][1] == 'a'*999
    doc_content = 'a'*999 + '\n' + 'b'*1000
    results = basic_tools.create_subdocuments(doc_name, doc_content)
    assert results[0][1] == 'a'*999 + '\n' + 'b'*1000

def test_remove_html_tags():
    text = '<html> <body>Some content &ldquo;</body></html>'
    result = basic_tools.remove_html_tags(text)
    assert result == ' Some content &ldquo;'
    text = '<html> <body>Some content &ldquo;</body>'
    result = basic_tools.remove_html_tags(text)
    assert result == ' Some content &ldquo;'

def test_replace_html_entities():
    text = u'<html> <body>Some content &pound;</body></html>'
    result = basic_tools.replace_html_entities(text)
    assert result == u'<html> <body>Some content \xA3</body></html>'

def test_get_unicode_content():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    directory = 'test_resources'
    path = os.path.join(root_dir, directory)
    utf8 = os.path.join(path, 'utf-8.txt')
    latin1 = os.path.join(path, 'latin_1.txt')
    
    expected_utf8 = u'random text: \xA3\xC1'
    expected_latin1 = u'random text: \xC1'
    
    with open(latin1, 'rb') as f:
        assert expected_latin1.encode(encoding='utf-8') != f.read()
    
    assert expected_utf8 == basic_tools.get_unicode_content(utf8)
    assert expected_latin1 == basic_tools.get_unicode_content(latin1)










