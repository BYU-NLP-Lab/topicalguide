from __future__ import print_function

import os
import sys
import json
from collections import defaultdict

from abstract_dataset import AbstractDataset, AbstractDocument
from analysis_settings import AnalysisSettings
from generic_tools import GenericTools

#TODO create an abstract base class


#A single object encapsulating every item necessary to import
#a dataset.  To create a customized Project class, just inherit from 
#this class and replace functions as needed.
class DataSetImportTask:
    """\
    Stores all of the critical information necessary for importing a dataset.
    """
    
    def __init__(self, project_directory):
        """\
        The project directory is a folder containing a "project_metadata.json" file, 
        and a folder called "documents" which contains the documents in the
        format specified in the README.txt file.
        """
        self.project_directory = project_directory
        self.project_metadata_file_name = 'project_metadata.json'
        self.dataset_folder = 'documents'
        self.dataset_directory = os.path.join(self.project_directory, \
                                               self.dataset_folder)
        self.dataset_name = 'some_data'
        self.number_of_topics = 50
        self.number_of_iterations = 100
        
        self.import_project_metadata()
        self.initialize_list_of_documents()
        self.analysis_settings = AnalysisSettings()
        
    def get_analysis_settings(self):
        return self.analysis_settings

    def initialize_list_of_documents(self):
        """\
        Gets a list of all files/documents that will be imported.
        """
        file_path = os.path.join(self.dataset_directory)
        self.list_of_documents = self.get_all_files(file_path)
        
    def get_all_files(self, file_path):
        """\
        Gets a list of ALL the files in the dataset.
        """
        all_files = []
        directories = []
        directories.append(file_path)
        
        while len(directories) > 0:
            file_path = directories.pop(0)
            all_files.extend(self.get_files(file_path))
            directories.extend(self.get_directories(file_path))
        return all_files
        
    def get_files(self, file_path):
        """\
        Gets a list of all files in the given directory.
        """
        files = [os.path.join(file_path, file_name) for file_name in os.listdir(file_path) \
                if self.is_valid_file(file_path, file_name)]
        return files
    
    def get_directories(self, file_path):
        """\
        Gets a list of all directories in the given directory.
        """
        dirs = [os.path.join(file_path, file_name) \
                for file_name in os.listdir(file_path) \
                if os.path.isdir(os.path.join(file_path, file_name))]
        return dirs
        
    def is_valid_file(self, file_path, file_name):
        """\
        Helper function to detect hidden files and folders.
        """
        is_dir = os.path.isfile(os.path.join(file_path, file_name))
        is_hidden_linux = file_name[0] != '.' and file_name[-1] != '~'
        return is_dir and is_hidden_linux
    
    def import_project_metadata(self):
        """\
        Opens the 'project_metadata.json file and imports the project metadata,
        the project metadata types, and the document types.
        """
        metadata_file_path = os.path.join(self.project_directory, \
                                        self.project_metadata_file_name)
        metadata_file = open(metadata_file_path, 'r')
        file_contents = metadata_file.read()
        metadata = json.loads(file_contents)
        self.project_metadata = metadata['data']
        self.project_metadataTypes = metadata['types']
        self.document_metadata_types = metadata['document_types']
    
    def get_number_of_topics(self):
        return self.number_of_topics
        
    def get_number_of_iterations(self):
        return self.number_of_iterations
    
    def get_number_of_documents(self):
        return len(self.list_of_documents)
    
    def get_document_metadata_types(self):
        return self.document_metadata_types
    
    def get_project_metadata_doc_types(self):
        return self.project_metadataDocTypes
    
    def get_project_name(self):
        return self.project_metadata['readable_name']
        
    def get_dataset_source(self):
        return self.project_metadata['source']
        
    def get_dataset_creator(self):
        return self.project_metadata['creator']
    
    def get_description(self):
        return self.project_metadata['description']
        
    def get_project_description(self):
        return self.project_metadata['description']
    
    def get_project_directory(self):
        return self.project_directory
    
    def get_dataset_name(self):
        """\
        This is for naming the working directory for this project.
        """
        return self.project_metadata['readable_name'].replace(' ', '_').lower()
        
    def get_dataset_readable_name(self):
        return self.project_metadata['readable_name']
    
    def replace_spaces(self, file_name):
        return file_name.replace(' ', '_')
    
    def get_all_documents_metadata(self):
        """\
        Collects all the documents' meta data.
        """
        all_document_metadata = {}
        for file_name in self.list_of_documents:
			try:
				newfile_name = os.path.split(self.replace_spaces(file_name))[-1]
				all_document_metadata[newfile_name] = self.get_document_metadata(file_name)
			except:
				continue
        return all_document_metadata
        
    def get_document_metadata(self, file_name):
        """\
        Gets the metadata from one document.
        """
        file_path = os.path.join(self.dataset_directory, file_name)
        with open(file_path, 'r') as document:
            file_contents = document.read()
        
        header = file_contents.split("\n\n", 1)
        
        if len(header) != 2:
			raise Exception("No metadata.")
        
        lines = header[0].splitlines()
        
        metadata = {}
        for line in lines:
            tokens = line.split(":")
            if len(tokens) == 2:
                header_id = tokens[0].strip().lower()
                if header_id in self.document_metadata_types:
                    metadata[header_id] = tokens[1].strip()
        return metadata
        
    def copy_contents_to_directory(self, dest_directory):
        """\
        Copies all of the documents data (no meta data included) to
        the specified directory.  Each file name should replace spaces
        with underscores.
        """
        
        for file_path in self.list_of_documents:
			file_name = os.path.split(file_path)[-1]
			new_file_name = self.replace_spaces(file_name)
			document = ""
			with open(file_path, 'r') as old_document:
				file_contents = old_document.read()
				temp = file_contents.split("\n\n", 1)
				document = temp[1]
			new_file_path = os.path.join(dest_directory, new_file_name)
			with open(new_file_path, 'w+') as new_document:
				new_document.write(document)
    

class GenericDataset(AbstractDataset):
    '''\
    The GenericDataset is an abstraction that allows the import process
    to interact with the dataset in a standardized manner. 
    This allows for flexibility in what datasets
    can be imported and how they are imported. 
    To create a class that imports
    data from a dataset with a different format or structure, extend this
    class and override functions as necessary.
    '''
    
    def __init__(self, dataset_directory):
        '''\
        dataset_directory: A relative or absolute file path to the \
        directory that contains the documents directory and the dataset_metadata.json file.
        Note that by default documents will be found by recursively searching the dataset_directory \
        and the documents don't have subdocuments.
        '''
        # create commonly used directory and file paths
        self.dataset_directory = os.path.abspath(dataset_directory)
        self.dataset_metadata_file = os.path.join(self.dataset_directory,
                                                  'dataset_metadata.json')
        self.documents_directory = os.path.join(self.dataset_directory, 
                                                'documents')
        
        self.does_have_subdocuments = False
        self.is_recursive = True
        
        # load the dataset metadata
        self.metadata = GenericTools.json_to_dict(self.dataset_metadata_file)
        self.dataset_metadata = self.metadata['data']
        self.dataset_metadata_types = self.metadata['types']
        self.document_metadata_types = self.metadata['document_types']
        
        # create/configure the analysis settings
        self.analysis_settings = AnalysisSettings()
    
    def set_has_subdocuments(self, does_have_subdocuments):
        '''\
        Setting this to True will indicate that Documents have subdocuments, and the \
        appropriate flags will be set.
        '''
        self.does_have_subdocuments = does_have_subdocuments
    
    def set_is_recursive(self, is_recursive):
        '''\
        Setting this to True will make the dataset class search for Documents recursively in the "documents" directory.
        '''
        self.is_recursive = is_recursive
    
    def get_analysis_settings(self):
        '''\
        Returns an AnalysisSettings object that tracks which analysis'
        to perform, specific file paths, etc.
        '''
        return self.analysis_settings
    
    def get_dataset_metadata(self):
        '''\
        Returns a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this dataset.
        Note that 'readable_name' and 'description' are special keys that are \
        used by the Topical Guide to neatly display an imported dataset.
        '''
        return self.dataset_metadata
    
    def get_dataset_identifier(self):
        '''\
        Returns a string that uniquely identifies this dataset on the \
        Topical Guide server.
        '''
        return self.dataset_metadata['readable_name'].replace(' ', '_').lower()
    
    def get_dataset_metadata_types(self):
        '''\
        Returns a dictionary where the keys are the metadata identifiers 
        for this dataset and the values are the types.
        '''
        return self.dataset_metadata_types
    
    def get_document_metadata_types(self):
        '''\
        Returns a dictionary where the keys are the metadata identifiers and
        the values are the types (e.g. "author": "string", "year": "int", etc.)
        '''
        return self.document_metadata_types
    
    def __iter__(self):
        '''\
        Returns a GenericDocument iterator.
        '''
        self.documents_index = 0
        self.list_of_documents = GenericTools.get_all_files_from_directory(self.documents_directory, self.is_recursive)
        return self
    
    def next(self):
        '''\
        Returns the next GenericDocument.  Files that cannot be opened \
        or raise an error will not be included.
        '''
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
    '''\
    While the GenericDataset is an abstraction of an entire dataset 
    the Document class is an abstraction of a single document in that dataset.
    '''
    
    def __init__(self, root_doc_directory, document_path):
        self.root_doc_directory = root_doc_directory
        self.document_path = document_path
        self.does_have_subdocuments = False
        
        with open(self.document_path, 'r') as doc_file:
            s = doc_file.read()
            metadata, self.content = GenericTools.seperate_metadata_and_content(s)
            self.metadata = GenericTools.metadata_to_dict(metadata)
    
    def set_has_subdocuments(self, does_have_subdocuments):
        '''\
        True indicates that this document has subdocuments.
        '''
        self.does_have_subdocuments = does_have_subdocuments
    
    def get_name(self):
        '''\
        Returns a unique identifier for this document.
        Must only contain underscores or alphanumeric characters.
        '''
        return os.path.relpath(self.document_path, self.root_doc_directory).replace('/', '_').replace(' ', '_')
    
    def get_metadata(self):
        '''\
        Returns a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        '''
        return self.metadata
    
    def get_content(self):
        '''\
        Returns the raw text of the document.
        '''
        return self.content
    
    def has_subdocuments(self):
        '''\
        Returns True if this document can be broken down into smaller \
        chunks/documents; False if the document cannot be broken down or \
        the user wants the entire document to be analyzed together.
        Must implement the __iter__ function if True is returned.
        Note that by default the subdocuments are
        '''
        return self.does_have_subdocuments
    
    def __iter__(self):
        '''\
        Returns a Document iterator where each document is a portion of
        the original one.
        '''
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
        '''\
        Returns a Document object representing a subdocument of this document.
        '''
        if self.subdocument_index < len(self.subdocuments_content):
            sub_doc = GenericSubdocument()
            sub_doc.set_content(self.subdocuments_content[self.subdocument_index])
            self.subdocument_index += 1
            return sub_doc
        raise StopIteration

class GenericSubdocument(GenericDocument):
    '''\
    Represents a subdocument.  This class doesn't allow for further subdocuments.
    '''
    def __init__(self):
        self.content = ''
        self.metadata = {}
    
    def set_content(self, content):
        self.content = content
    
    def has_subdocuments(self):
        return False

