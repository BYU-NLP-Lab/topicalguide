from __future__ import print_function

import os
import sys

from import_tool import basic_tools
from abstract_dataset import AbstractDataset, AbstractDocument
    

class GenericDataset(AbstractDataset):
    """
    The GenericDataset allows the import process
    to interact with the dataset in a standardized/pre-determined manner. 
    """
    
    def __init__(self, dataset_directory):
        """
        dataset_directory: A relative or absolute file path to the \
        directory that contains the documents directory and the dataset_metadata.txt file.
        By default documents will be found recursively.
        """
        # create commonly used directory and file paths
        self.dataset_directory = dataset_directory
        self.abs_dataset_directory = os.path.abspath(dataset_directory)
        self.metadata_file = os.path.join(self.abs_dataset_directory,
                                          'dataset_metadata.txt')
        self.documents_directory = os.path.join(self.abs_dataset_directory, 
                                                'documents')
        self.is_recursive = True
        
        self.metadata = {}
        # load the dataset metadata
        with open(self.metadata_file, 'r') as meta_file:
            content = meta_file.read()
            metadata, __ = basic_tools.seperate_metadata_and_content(content)
            self.metadata = basic_tools.metadata_to_dict(metadata)
        
        if not 'readable_name' in self.metadata:
            identifier = self.dataset_directory.replace('_', ' ').replace('/', ' ').title()
        else:
            identifier = self.metadata['readable_name']
        self.set_identifier(basic_tools.remove_punctuation(identifier))
        
        # used to efficiently retreive the length after it is computed the first time
        self.length = None
    
    @property
    def readable_name(self):
        if 'readable_name' in self.metadata:
            return self.metadata['readable_name']
        else:
            return self.identifier.replace('_', ' ').title()
    
    @property
    def description(self):
        if 'description' in self.metadata:
            return self.metadata['description']
        else: 
            return 'No description available.'
    
    def set_is_recursive(self, is_recursive):
        """
        Setting this to True will make the dataset class search for Documents recursively in the "documents" directory.
        """
        self.is_recursive = is_recursive
    
    def set_identifier(self, identifier):
        """
        Set the dataset identifier used in the database and elsewhere.
        Note that all spaces and slashes will be replaced with underscores and the name will be set to lowercase.
        The use of symbols other than '_' and '-' is discouraged.
        """
        self.identifier = identifier.replace(' ', '_').replace('/', '_').lower()
    
    def get_metadata(self):
        """
        Return a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this dataset.
        Note that 'readable_name' and 'description' are special keys that are \
        used by the Topical Guide to neatly display an imported dataset.
        """
        return self.metadata
    
    def get_identifier(self):
        """
        Return a string that uniquely identifies this dataset on the \
        Topical Guide server.
        """
        return self.identifier
    
    def __len__(self):
        """Return the total number of documents."""
        if self.length:
            return self.length
        count = 0
        for doc in self:
            count += 1
        self.length = count
        return count
    
    def __iter__(self):
        """Return a GenericDocument iterator."""
        self.documents_index = 0
        self.list_of_documents = basic_tools.get_all_files_from_directory(self.documents_directory, self.is_recursive)
        return self
    
    def next(self):
        """
        Return the next GenericDocument.  Files that cannot be opened \
        or raise an error will not be included.
        """
        while self.documents_index < len(self.list_of_documents):
            index = self.documents_index
            self.documents_index += 1
            file_path = self.list_of_documents[index]
            try:
                document = GenericDocument(self.documents_directory, file_path)
                return document
            except Exception as e:
                print('Error: Could not import %s because of %s' % (file_path, e))
        raise StopIteration
        

class GenericDocument(AbstractDocument):
    """
    While the GenericDataset is an abstraction of an entire dataset 
    the Document class is an abstraction of a single document in that dataset.
    """
    
    def __init__(self, root_doc_directory, document_path):
        self.root_doc_directory = root_doc_directory
        self.document_path = document_path
        self.content = ''
        self.metadata = {}
        
        text = ''
        with open(document_path, 'r') as f:
            text = unicode(f.read(), encoding='utf-8', errors='ignore')
        metadata, self.content = basic_tools.seperate_metadata_and_content(text)
        self.metadata = basic_tools.metadata_to_dict(metadata)
    
    def get_identifier(self):
        """
        Return a unique identifier for this document.
        Must only contain underscores or alphanumeric characters.
        """
        return os.path.relpath(self.document_path, self.root_doc_directory).replace('/', '_').replace(' ', '_')
    
    def get_uri(self):
        """Return the document's uri."""
        return os.path.abspath(self.document_path)
    
    def get_metadata(self):
        """
        Return a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        """
        return self.metadata
    
    def get_content(self):
        """Returns the raw text of the document in a utf-8 encoding."""
        return self.content


