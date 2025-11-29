import os
import io
import json
from import_tool import basic_tools
from .generic_dataset import GenericDataset, GenericDocument


class JsonDataset(GenericDataset):
    """The JsonDataset expects all data to be in a json format."""
    
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
                                           'dataset_metadata.json')
        self._documents_directory = os.path.join(self._abs_dataset_directory, 
                                                 'documents')
        self.is_recursive = is_recursive
        self._filters = []
        
        self.metadata = {}
        # load the dataset metadata
        with io.open(self.metadata_file, 'r', encoding='utf-8') as meta_file:
            self.metadata = json.loads(meta_file.read())['dataset_metadata']
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
    
    def next(self):
        """
        Return the next JsonDocument.  Files that cannot be opened \
        or raise an error will not be included.
        """
        while self._documents_index < len(self._list_of_documents):
            file_path = self._list_of_documents[self._documents_index]
            self._documents_index += 1
            try:
                document = JsonDocument(self._documents_directory, file_path)
                document.set_filters(self._filters)
                return document
            except Exception as e:
                print('Error: Could not import %s because of %s' % (file_path, e))
        raise StopIteration


class JsonDocument(GenericDocument):
    """
    While the JsonDataset is an abstraction of an entire dataset 
    the Document class is an abstraction of a single document 
    in that dataset.
    """
    
    def __init__(self, root_doc_directory, document_path):
        super(GenericDocument, self).__init__(root_doc_directory, document_path)
    
    def _read_document(self):
        """Must set the self._content and self._metadata variables."""
        with open(document_path, 'r') as f:
            document = json.loads(f.read())
            self._metadata = document['metadata']
            content = document['content']
            for filt in self._filters:
                content = filt(content)
            self._content = content
