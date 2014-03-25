from __future__ import print_function

import os
import sys
import json
from collections import defaultdict

from abstract_dataset import AbstractDataset, AbstractDocument
from analysis_settings import AnalysisSettings
from generic_tools import GenericTools
    

class GenericDataset(AbstractDataset):
    """
    The GenericDataset allows the import process
    to interact with the dataset in a standardized/pre-determined manner. 
    """
    
    def __init__(self, dataset_directory):
        """
        dataset_directory: A relative or absolute file path to the \
        directory that contains the documents directory and the dataset_metadata.txt file.
        Note that by default documents will be found by recursively searching the dataset_directory \
        and the documents don't have subdocuments.
        """
        # create commonly used directory and file paths
        self.dataset_directory = dataset_directory
        self.abs_dataset_directory = os.path.abspath(dataset_directory)
        self.metadata_file = os.path.join(self.abs_dataset_directory,
                                          'dataset_metadata.txt')
        self.documents_directory = os.path.join(self.abs_dataset_directory, 
                                                'documents')
        
        self.does_have_subdocuments = False
        self.is_recursive = True
        
        self.metadata = {}
        # load the dataset metadata
        with open(self.metadata_file, 'r') as meta_file:
            metadata, __ = GenericTools.seperate_metadata_and_content(meta_file.read())
            self.metadata = GenericTools.metadata_to_dict(metadata)
        
        if not 'readable_name' in self.metadata:
            self.readable_name = self.dataset_directory.replace('_', ' ').replace('/', ' ').title()
        else:
            self.readable_name = self.metadata['readable_name']
            del self.metadata['readable_name']
        
        if not 'description' in self.metadata:
            self.description = 'No description.'
        else:
            self.description = self.metadata['description']
            del self.metadata['description']
        
        self.set_identifier(self.readable_name)
    
    def set_has_subdocuments(self, does_have_subdocuments):
        """
        Setting this to True will indicate that Documents have \
        subdocuments, and the appropriate flags will be set.
        """
        self.does_have_subdocuments = does_have_subdocuments
    
    def set_is_recursive(self, is_recursive):
        """
        Setting this to True will make the dataset class search for Documents recursively in the "documents" directory.
        """
        self.is_recursive = is_recursive
    
    def set_identifier(self, identifier):
        """
        Sets the dataset identifier used in the database and elsewhere.
        Note that all spaces and slashes will be replaced with underscores and the name will be set to lowercase.
        The use of symbols other than '_' and '-' is discouraged.
        """
        self.identifier = identifier.replace(' ', '_').replace('/', '_').lower()
    
    def get_metadata(self):
        """
        Returns a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this dataset.
        Note that 'readable_name' and 'description' are special keys that are \
        used by the Topical Guide to neatly display an imported dataset.
        """
        return self.metadata
    
    def get_identifier(self):
        """
        Returns a string that uniquely identifies this dataset on the \
        Topical Guide server.
        """
        return self.identifier
    
    def get_readable_name(self):
        return self.readable_name
    
    def get_description(self):
        return self.description
    
    def __iter__(self):
        """Return a GenericDocument iterator."""
        self.documents_index = 0
        self.list_of_documents = GenericTools.get_all_files_from_directory(self.documents_directory, self.is_recursive)
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
                document.set_has_subdocuments(self.does_have_subdocuments)
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
        self.does_have_subdocuments = False
        
        self.content = None
        self.metadata = None
        
    
    def get_file_text(self):
        """Set self.content and self.metadata. Load file content lazily."""
        if self.content is None or self.metadata is None:
            self.content = ''
            self.metadata = {}
            with open(self.document_path, 'r') as doc_file:
                s = doc_file.read()
                metadata, self.content = GenericTools.seperate_metadata_and_content(s)
                self.metadata = GenericTools.metadata_to_dict(metadata)
    
    def set_has_subdocuments(self, does_have_subdocuments):
        """True indicates that this document has subdocuments."""
        self.does_have_subdocuments = does_have_subdocuments
    
    def get_identifier(self):
        """
        Returns a unique identifier for this document.
        Must only contain underscores or alphanumeric characters.
        """
        return os.path.relpath(self.document_path, self.root_doc_directory).replace('/', '_').replace(' ', '_')
    
    def get_uri(self):
        """
        Returns the document's uri.
        """
        return os.path.abspath(self.document_path)
    
    def get_metadata(self):
        """
        Returns a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        """
        self.get_file_text()
        return self.metadata
    
    def get_content(self):
        """Returns the raw text of the document."""
        self.get_file_text()
        return self.content
    
    def has_subdocuments(self):
        """
        Returns True if this document can be broken down into smaller \
        chunks/documents; False if the document cannot be broken down or \
        the user wants the entire document to be analyzed together.
        Must implement the __iter__ function if True is returned.
        Note that by default the subdocuments are
        """
        return self.does_have_subdocuments
    
    def __iter__(self):
        """
        Returns a Document iterator where each document is a portion of
        the original one.
        """
        self.get_file_text()
        
        if self.does_have_subdocuments:
            subdoc_content_temp = self.content.split('\n\n')
            self.subdocuments_content = []
            for sub_doc in subdoc_content_temp:
                sub_doc = sub_doc.strip()
                if sub_doc != '':
                    self.subdocuments_content.append(sub_doc)
            self.subdocument_index = 0
            return self
        else:
            raise Exception('Not able to split into subdocuments.')
    
    def next(self):
        """
        Returns a Document object representing a subdocument of this document.
        """
        if self.subdocument_index < len(self.subdocuments_content):
            sub_doc = GenericSubdocument()
            sub_doc.set_identifier(str(self.subdocument_index) + '-' + self.get_identifier())
            sub_doc.set_content(self.subdocuments_content[self.subdocument_index])
            sub_doc.set_metadata(self.get_metadata())
            sub_doc.set_uri(os.path.abspath(self.document_path))
            self.subdocument_index += 1
            return sub_doc
        raise StopIteration

class GenericSubdocument(GenericDocument):
    """
    Represents a subdocument.  This class doesn't allow for further subdocuments.
    """
    def __init__(self):
        self.content = ''
        self.metadata = {}
        self.name = ''
    
    def set_identifier(self, identifier):
        self.identifier = identifier
    
    def get_identifier(self):
        return self.identifier
    
    def set_content(self, content):
        self.content = content
    
    def set_metadata(self, metadata):
        self.metadata = metadata
    
    def set_uri(self, path):
        self.document_path = path
        
    def get_uri(self):
        self.document_path
    
    def has_subdocuments(self):
        return False

