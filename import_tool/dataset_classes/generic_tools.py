from __future__ import print_function

import os
import json


class GenericTools:
    
    @staticmethod
    def convert_types(types, metadata):
        '''\
        Takes two dictionaries, types and metadata.  The types dictionary \
        tells what types the metadata should be and this method will perform the \
        necessary conversions.  Note that the contents of metadata will be modified directly.
        Currently only 'text' and 'int' types are handled.
        All metadata types should be strings to begin with.
        No errors are caught or handled if the conversion fails.
        Returns nothing.
        '''
        for type_key in types:
            if type_key in metadata:
                if types[type_key] == 'int':
                    metadata[type_key] = int(metadata[type_key])
    
    @staticmethod
    def json_to_dict(file_path):
        '''\
        Takes a file path to a .json file and converts the contents to a dictionary.
        If an error occurs, an empty dictionary is returned.
        '''
        try:
            result = {}
            with open(file_path, 'r') as json_file:
                file_contents = json_file.read()
                result = json.loads(file_contents)
            return result
        except Exception:
            return {}
    
    @staticmethod
    def dict_to_json(d, file_path):
        '''\
        Takes a dictionary d and a file path and writes the dictionary to the file in a \
        json format.
        '''
        with open(file_path, 'w') as meta_file:
            meta_file.write(json.dumps(d))
    
    @staticmethod
    def seperate_metadata_and_content(s):
        '''\
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
        '''
        m_and_c = s.split("\n\n", 1)
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
                    key_value = l.split(':')
                    if len(key_value) != 2:
                        is_metadata = False
                        break
                
                if is_metadata:
                    metadata = value
                else:
                    content = value
        
        return (metadata, content)
    
    @staticmethod
    def metadata_to_dict(metadata):
        '''\
        Takes metadata as specified in seperate_metadata_and_content() documentation and\
        converts it to a dictionary.
        Note that white space on either side of the metadata tags and values will be stripped; \
        also, if there are any duplicate metadata key names, the value of the last duplicate will \
        be in the resulting dictionary.
        Also, the tags will have any spaces replaced with underscores and be set to lowercase.
        '''
        result = {}
        lines = metadata.split('\n')
        for l in lines:
            key_value = l.split(':', 1)
            if len(key_value) == 2:
                key = key_value[0].strip().replace(' ', '_').lower()
                value = key_value[1].strip()
                result[key] = value
        return result
    
    @staticmethod
    def get_all_files_from_directory(directory, recursive=False):
        '''\
        Set recursive to True to recursively find files.
        Return a list of absolute file paths starting at the given directory.
        '''
        list_of_files = []
        
        for root, dirs, files in os.walk(directory, followlinks=recursive):
            for file in files:
                list_of_files.append(os.path.join(root, file))
        return list_of_files
    
    @staticmethod
    def walk_documents(documents, action, arg):
        '''\
        Iterates through documents, which must return objects of type AbstractDocument, and \
        executes the action method (Template Method design pattern.)
        The method will be called as follows: action(arg, doc_identifier, doc_uri, doc_metadata, doc_content) \
        where arg is the same arg passed to this method and doc_metadata is a document's metadata \
        and doc_content is a document's content.
        Returns None.
        '''
        for doc in documents:
            if not doc.has_subdocuments():
                action(arg, doc)
            else:
                subdoc_metadata = GenericTools.walk_documents(doc, action, arg)
    
    @staticmethod
    def get_type(value):
        '''\
        Returns the type of value, value is a string.
        Returns one of the known types in the form of a string: 'int', 'float', 'bool', and 'text'.
        Example: If value = '34' then the type returned is 'int'.
        '''
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
        value = value.lower()
        if value == 'true' or value == 'false' or value == 't' or value == 'f':
            return 'bool'
        return 'text'
    
    @staticmethod
    def collect_types(metadata_types, metadata):
        '''\
        Takes a dictionary metadata_types that keeps track of the types so far.
        For each key, value pair in metadata if the key is not present in \
        metadata_types then it is added and the type of the value is also added.
        Note that if there are conflicting types then the type in metadata_types is
        degraded to 'text'.
        '''
        for meta_key in metadata:
            t = GenericTools.get_type(metadata[meta_key])
            if not meta_key in metadata_types:
                metadata_types[meta_key] = t
            else:
                if not metadata_types[meta_key] == t:
                    if t == 'float' and metadata_types[meta_key] == 'int':
                        metadata_types[meta_key] = 'float'
                    elif t == 'int' and metadata_types[meta_key] == 'float':
                        pass
                    else:
                        metadata_types[meta_key] = 'text'




# vim: et sw=4 sts=4
