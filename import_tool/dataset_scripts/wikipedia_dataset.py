from __future__ import print_function

import os
import sys

from import_tool import basic_tools
from abstract_dataset import AbstractDataset, AbstractDocument


class WikipediaDataset(AbstractDataset):
    """Create an interface between the import pipeline and Wikipedia.org."""
    
    def __init__(self, identifier, user, email):
        """
        Create empty set of page titles and usual variables; \
        identifier must be a unique string in the context of Dataset filenames.
        """
        self.titles = set()
        self.readable_name = ''
        self.description = ''
        set_identifier(identifier)
        self.user = user
        self.email = email
    
    def set_settings_directory(self, directory):
        """Extract dataset metadata and any page titles (if any) from the given directory."""
        self.abs_directory = os.path.abspath(directory)
        self.metadata_file = os.path.join(self.abs_directory,
                                          'dataset_metadata.txt')
        self.pages_file = os.path.join(self.abs_directory, 'pages.txt')
        self.metadata = {}
        # load the dataset metadata
        with open(self.metadata_file, 'r') as meta_file:
            metadata, __ = GenericTools.seperate_metadata_and_content(meta_file.read())
            self.metadata = GenericTools.metadata_to_dict(metadata)
        
        if not 'readable_name' in self.metadata:
            self.readable_name = self.directory.replace('_', ' ').replace('/', ' ').title()
        else:
            self.readable_name = self.metadata['readable_name']
            del self.metadata['readable_name']
        
        if not 'description' in self.metadata:
            self.description = 'No description.'
        else:
            self.description = self.metadata['description']
            del self.metadata['description']
        
        # load any specified urls
        if os.path.exists(self.pages_file):
            with open(self.pages_file, 'r') as f:
                lines = f.read().split()
                for line in lines:
                    line = line.strip()
                    if line != '':
                        self.titles.add(line)
    
    def add_title(self, title):
        """Strip out any url and add just the title."""
        # TODO give this function functionality
        pass
    
    def populate_by_recursion(self, title, depth, limit):
        """
        Get page titles by collecting titles from the single given title.
        Continue collection until the depth is reached or the limit of
        titles is reached.  The limit refers to the amount collected in this method
        and ignores any pre-existing titles.
        """
        # TODO make this work
        pass
    
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
        Return the next WikipediaDocument.  Files that cannot be opened \
        or raise an error will not be included.
        """
        for title in self.titles:
            try:
                document = WikipediaDocument(title, self.user, self.email)
                yield document
            except Exception as e:
                print('Error: Could not import %s because of %s' % (file_path, e))
        raise StopIteration
        

class WikipediaDocument(AbstractDocument):
    """Create an interface to a single Wikipedia page."""
    
    def __init__(self, title, user, email):
        """
        Get the document contents and metadata.
        Where the WikipediaDataset is robust with titles, this class will
        only take a title (no url type format).
        """
        self.title = title
        self.content = ''
        self.metadata = {}
    
    def get_identifier(self):
        return self.title
    
    def get_uri(self):
        return "https://en.wikipedia.org/wiki/" + self.title
    
    def get_metadata(self):
        return self.metadata
    
    def get_content(self):
        return self.content
    
    


