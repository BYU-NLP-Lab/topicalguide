
import os
import io
import json
import random
from import_tool import basic_tools
from .abstract_dataset import AbstractDataset, AbstractDocument


# Range of regular punctuation, 
ASCII_MIN = 32 # Space
ASCII_MAX = 126 # Tilde
ASCII_NEWLINE = 127 # Not actual ascii decimal value
ASCII_TAB = 128 # Not actual ascii decimal value


class RandomDataset(AbstractDataset):
    """Random data can help find edge cases and perform stress testing.
    
    The directory should contain a 'settings.json' file. If not then the
    defaults are used.
    Examples of settings required keys include:
    name
    number_of_documents
    document_length
    seed
    """
    def __init__(self, dataset_directory, **kwargs):
        self._dataset_directory = dataset_directory
        self._abs_dataset_directory = os.path.abspath(dataset_directory)
        self._settings_file = os.path.join(self._abs_dataset_directory, 'settings.json')
        if os.path.exists(self._settings_file):
            with io.open(self._settings_file, 'r', encoding='utf-8') as f:
                self._settings = json.loads(f.read())['settings']
        else:
            self._settings = {}
        
        self.metadata_types = {}
        self.metadata = self._settings
        basic_tools.collect_types(self.metadata_types, self.metadata)
        self.document_metadata_types = {'meta': 'text'}
        
        self.name = self._settings.setdefault('name', 'random')
        self.number_of_documents = self._settings.setdefault('number_of_documents', 1000)
        self.document_length = self._settings.setdefault('document_length', 1000)
        self.seed = self._settings.setdefault('seed', 0)
    
    def __iter__(self):
        """Return an AbstractDocument iterator that iterates over 
        documents in alphabetical order.
        """
        self.doc_index = 0
        random.seed(self.seed)
        return self
    
    def next(self):
        if self.doc_index >= self.number_of_documents:
            raise StopIteration
        else:
            doc = RandomDocument(self.document_length)
            doc.name = 'Document ' + str(self.doc_index)
            doc.source = 'Random Document #' + str(self.doc_index)
            self.doc_index += 1
            return doc
    
    def __len__(self):
        """Return the number of documents to be imported."""
        return self.number_of_documents


class RandomDocument(AbstractDocument):
    def __init__(self, document_length):
        self.name = ''
        self.source = None
        self.content = ''
        for i in range(0, document_length):
            r = random.randint(ASCII_MIN, ASCII_MAX+2)
            if r <= ASCII_MAX:
                self.content += chr(r)
            elif r == ASCII_NEWLINE:
                self.content += '\n'
            elif r == ASCII_TAB:
                self.content += '\t'
        self.content = str(self.content)
        self.metadata = {'meta': 'nothing'}

