from __future__ import division, print_function, unicode_literals
import os
import io
from import_tool import basic_tools
from abstract_dataset import AbstractDataset, AbstractDocument
    

class GenericDataset(AbstractDataset):
    """
    The GenericDataset allows the import process to interact with the 
    dataset in a standardized/pre-determined manner.  See the wiki
    for more details on dataset format.
    """
    
    def __init__(self, dataset_directory, is_recursive=True):
        """
        dataset_directory -- a relative or absolute file path to the \
        directory that contains the documents directory and the dataset_metadata.txt file.
        is_recursive -- find documents recursively in the documents directory, \
                        by default documents will be found recursively.
        Document metadata types will be infered from the document metadata.
        """
        # create commonly used directory and file paths
        self._dataset_directory = dataset_directory
        self._abs_dataset_directory = os.path.abspath(dataset_directory)
        self._metadata_file = os.path.join(self._abs_dataset_directory,
                                           'dataset_metadata.txt')
        self._documents_directory = os.path.join(self._abs_dataset_directory, 
                                                 'documents')
        self.is_recursive = is_recursive
        self._filters = []
        
        self.metadata = {}
        # load the dataset metadata
        with io.open(self._metadata_file, 'r', encoding='utf-8', errors='ignore') as meta_file:
            content = meta_file.read()
            metadata, __ = basic_tools.seperate_metadata_and_content(content)
            self.metadata = basic_tools.metadata_to_dict(metadata)
        self.metadata_types = {}
        basic_tools.collect_types(self.metadata_types, self.metadata)
        
        if not 'readable_name' in self.metadata:
            identifier = self._dataset_directory.replace('_', ' ').replace('/', ' ').title()
        else:
            identifier = self.metadata['readable_name']
        self.name = basic_tools.remove_punctuation(identifier)
        
        # find and sort all file paths
        self._list_of_documents = basic_tools.get_all_files_from_directory(self._documents_directory, self.is_recursive)
        self._list_of_documents.sort()
        
        # find any bad documents and find document metadata
        self.document_metadata_types = {}
        bad_doc_indices = []
        for doc_index, doc in enumerate(self):
            try:
                basic_tools.collect_types(self.document_metadata_types, doc.metadata)
            except Exception as e:
                print("Bad document: ", self._list_of_documents[doc_index])
                bad_doc_indices.append(doc_index)
        while len(bad_doc_indices) != 0:
            remove_index = bad_doc_indices.pop()
            del self._list_of_documents[remove_index]
    
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, identifier):
        """Set the dataset identifier used in the database and elsewhere.
        Note that all spaces and slashes will be replaced with underscores 
        and the name will be set to lowercase.
        The use of symbols other than '_' and '-' is discouraged.
        """
        self._name = identifier.replace(' ', '_').replace('/', '_').lower()
    
    def add_text_filters(self, filters=[]):
        self._filters.extend(filters)
    
    def __len__(self):
        return len(self._list_of_documents)
    
    def __iter__(self):
        self._documents_index = 0
        return self
    
    def next(self):
        """
        Return the next GenericDocument.  Files that cannot be opened \
        or raise an error will not be included.
        """
        while self._documents_index < len(self._list_of_documents):
            file_path = self._list_of_documents[self._documents_index]
            self._documents_index += 1
            try:
                document = GenericDocument(self._documents_directory, file_path)
                document.set_filters(self._filters)
                return document
            except Exception as e:
                print('Error: Could not import %s because of %s' % (file_path, e))
        raise StopIteration

class GenericDocument(AbstractDocument):
    """
    While the GenericDataset is an abstraction of an entire dataset 
    the Document class is an abstraction of a single document 
    in that dataset.
    """
    
    def __init__(self, root_doc_directory, document_path):
        self._root_doc_directory = root_doc_directory
        self._document_path = document_path
        self._filters = []
        self._content = None
        self._metadata = None
    
    def set_filters(self, filters):
        """A list of functions taking a unicode string and returning a unicode string."""
        self._filters = filters
    
    @property
    def name(self):
        """
        Return a unique identifier for this document.
        Must only contain underscores or alphanumeric characters.
        """
        return os.path.relpath(self._document_path, self._root_doc_directory).replace('/', '_').replace(' ', '_')
    
    @property
    def source(self):
        """Return the document's uri."""
        return None
    
    def _read_document(self):
        """Must set the self._content and self._metadata variables."""
        with io.open(self._document_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        metadata, content = basic_tools.seperate_metadata_and_content(text)
        self._metadata = basic_tools.metadata_to_dict(metadata)
        for f in self._filters:
            content = f(content)
        self._content = content
    
    @property
    def metadata(self):
        """
        Return a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        """
        if self._metadata is not None:
            return self._metadata
        self._read_document()
        return self._metadata
    
    @property
    def content(self):
        """Returns the raw text of the document in a utf-8 encoding."""
        if self._content is not None:
            return self._content
        self._read_document()
        return self._content


