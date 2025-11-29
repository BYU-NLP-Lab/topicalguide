import os
import re
import html
from dateutil.parser import parse as dateutil_parse
from html.parser import HTMLParser


def seperate_metadata_and_content(s):
    """
    Given a string the metadata is seperated from the content. The string must be in the following format:
    
    metadata_tag1: metadata_value1
    metadata_tag2: metadata_value2
    ...
    metadata_tagn: metadata_valuen
    <Two newlines>
    content
    content
    
    content
    ...
    
    Returns (metadata, content)
    
    If no metadata is present then an empty string is returned, same with content.
    """
    m_and_c = s.split('\n\n', 1)
    metadata = ''
    content = ''
    
    # normal case where we have metadata and content
    if len(m_and_c) == 2:
        metadata = m_and_c[0].strip()
        content = m_and_c[1].strip()
    # if we only have one of content or metadata this process determines which it is
    elif len(m_and_c) == 1:
        value = m_and_c[0].strip()
        if not len(value) == 0:
            lines = value.split('\n')
            is_metadata = True
            for l in lines:
                key_value = l.split(':', 1)
                if len(key_value) != 2:
                    is_metadata = False
                    break
            
            if is_metadata:
                metadata = value
            else:
                content = value
    
    return (metadata, content)

def metadata_to_dict(metadata):
    """
    Takes metadata as specified in seperate_metadata_and_content() documentation and\
    converts it to a dictionary.
    Note that white space on either side of the metadata tags and values will be stripped; \
    also, if there are any duplicate metadata key names, the value of the last duplicate will \
    be in the resulting dictionary.
    Also, the tags will have any spaces replaced with underscores and be set to lowercase.
    """
    result = {}
    lines = metadata.split('\n')
    for l in lines:
        key_value = l.split(':', 1)
        if len(key_value) == 2:
            key = key_value[0].strip().replace(' ', '_').lower()
            value = key_value[1].strip()
            result[key] = value
    return result

def get_all_files_from_directory(directory, recursive=False):
    """
    Set recursive to True to recursively find files.
    Return a list of absolute file paths starting at the given directory.
    """
    list_of_files = []
    
    for root, dirs, files in os.walk(directory, followlinks=recursive):
        for file in files:
            list_of_files.append(os.path.join(root, file))
    return list_of_files

def get_type(value):
    """
    Returns the type of value, value is a string.
    Returns one of the known types in the form of a string: 'int', 'float', 'bool', and 'text'.
    Example: If value = '34' then the type returned is 'int'.
    """
    try:
        int(value)
        return 'int'
    except:
        pass
    try:
        float(value)
        return 'float'
    except:
        pass
    lower_value = value.lower()
    if lower_value == 'true' or lower_value == 'false' or lower_value == 't' or lower_value == 'f':
        return 'bool'
    try:
        dateutil_parse(value)
        return 'datetime'
    except:
        pass
    return 'text'

def collect_types(metadata_types, metadata):
    """
    Takes a dictionary metadata_types that keeps track of the types so far.
    For each key, value pair in metadata if the key is not present in \
    metadata_types then it is added and the type of the value is also added.
    Note that if there are conflicting types then the type in metadata_types is \
    degraded to 'text'.
    """
    for meta_key in metadata:
        t = get_type(metadata[meta_key])
        if not meta_key in metadata_types:
            metadata_types[meta_key] = t
        else:
            if not metadata_types[meta_key] == t and metadata_types[meta_key] != 'text':
                if t == 'float' and metadata_types[meta_key] == 'int':
                    metadata_types[meta_key] = 'float'
                elif t == 'int' and metadata_types[meta_key] == 'float':
                    pass
                elif t == 'text' and metadata_types[meta_key] == 'date':
                    metadata_types[meta_key] = 'date'
                else:
                    metadata_types[meta_key] = 'text'

def create_subdocuments(name, content, major_delimiter='\n', min_chars=1000):
    """
    Return a list of tuples where each tuple contains a subdocument name \
    and a subsequence of the original content.  Recombining each subdocument \
    content in the order the list is iterated over will yield the original content \
    (with varying white space.)  The arguments min and max specify the allowed sizes of \
    each subdocument by character count.  Note that the max may be exceeded on some occassions \
    if the remaining text doesn't consititute enough for another subdocument.  The \
    basic algorithm tries to split on new line boundaries since spliting on \
    white space alone may generate odd subdocuments.
    """
    subdoc_contents = {}
    subdoc_number = 0
    
    if content == '':
        subdoc_contents[subdoc_number] = ''
        subdoc_number += 1
    
    while content != '':
        #~ content = content.strip()
        index = 0
        while index < min_chars:
            index = content.find(major_delimiter, index + 1)
            if index < 0:
                # No delimiter found, add remaining content (strip trailing delimiter if present)
                subdoc_contents[subdoc_number] = content.rstrip(major_delimiter)
                subdoc_number += 1
                content = ''
                break
            elif index >= min_chars:
                subdoc_contents[subdoc_number] = content[0: index]
                content = content[index + len(major_delimiter):]
                if len(content) < min_chars:
                    subdoc_contents[subdoc_number] = subdoc_contents[subdoc_number] + content
                    content = ''
                subdoc_number += 1
    
    result = []
    for index in range(0, subdoc_number):
        result.append((name + '_subdoc' + str(index), subdoc_contents[index]))
    return result

def remove_html_tags(text, remove_entities=False):
    """Return string that has no HTML tags and removes HTML entities if specified."""
    class HTMLStripper(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.content = []
        def handle_data(self, data):
            self.content.append(data)
        def handle_entityref(self, name):
            if not remove_entities:
                self.content.append('&' + name + ';')
        def handle_charref(self, name):
            if not remove_entities:
                self.content.append('&#' + name + ';')
        def get_content(self):
            return ''.join(self.content)
    stripper = HTMLStripper()
    stripper.feed(text)
    stripper.close()
    return stripper.get_content()

def replace_html_entities(text):
    """Return string with HTML entities replaced with unicode characters."""
    return html.unescape(text)

def get_unicode_content(file_path, encoding=None):
    """
    Return a unicode string of the files contents using the given encoding.  If no encoding is given
    then chardet will be used to determine the encoding.
    Note that this uses the chardet library and may cause problems, if an error is thrown then
    a utf-8 encoding is assumed and unrecognize caracters are discarded.
    """
    from chardet.universaldetector import UniversalDetector
    
    try:
        if not encoding:
            detector = UniversalDetector()
            contents = ''
            with open(file_path, 'rb') as f:
                contents = f.read()
                detector.feed(contents)
            detector.close()
            determined_encoding = detector.result['encoding']
            return contents.decode(encoding=determined_encoding)
        else:
            with open(file_path, 'r') as f:
                return str(f.read(), encoding=encoding, errors='ignore')
    except UnicodeError:
        with open(file_path, 'r') as f:
            return str(f.read(), encoding='utf-8', errors='ignore')

def remove_punctuation(s):
    """Return a string without punctuation (only alpha, numeric, underscore and whitespace characters survive)."""
    result = ''
    for sub in re.finditer(r'[\w\s]+', s, re.UNICODE):
        result += sub.group(0)
    return result

# vim: et sw=4 sts=4
