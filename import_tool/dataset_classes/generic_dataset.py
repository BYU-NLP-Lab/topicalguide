#The following object is a way to make data importing easier.

#TODO create base class that has virtual functions required by the 
#import process
#TODO remove helper functions to helper library
#TODO documents which methods are required by the import process, mallet,
#analysis tools, etc.

from __future__ import print_function
import os
import sys
import json
from collections import defaultdict
from generic_tools import GenericTools


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
    

class GenericDataset:
    '''\
    The DataSetImportTask is an abstraction that allows the import process
    to interact with the dataset in a standardized manner. 
    This allows for flexibility in what datasets
    can be imported and how they are imported. 
    To create a class that imports
    data from a dataset with a different format or structure, extend this
    class and override functions as necessary.
    '''
    
    def __init__(self, dataset_directory, subdocuments, recursive):
        '''\
        dataset_directory: a relative or absolute file path to the 
        directory that contains the documents directory and the dataset_metadata.json file
        subdocuments: a boolean flag that indicate whether or not you want to 
        break documents down into subdocuments
        recursive: a boolean flag indicating whether or not 
        
        '''
        # create commonly used directory and file paths
        self.dataset_directory = os.path.abspath(dataset_directory)
        self.dataset_metadata_file = os.path.join(self.dataset_directory,
                                                  'dataset_metadata.json')
        self.documents_directory = os.path.join(self.dataset_directory, 
                                                'documents')
        
        self.subdocuments = subdocuments
        self.recursive = recursive
        
        # load the dataset metadata
        self.metadata = GenericTools.json_to_dict(dataset_metadata_file)
        self.dataset_metadata = metadata['data']
        self.dataset_metadata_types = metadata['types']
        self.document_metadata_types = metadata['document_types']
        # TODO make all key values lowercase, with no spaces
        
        # create/configure the analysis settings
        self.analysis_settings = AnalysisSettings()
    
    def get_analysis_settings(self):
        '''\
        Returns an AnalysisSettings object that tracks which analysis'
        to perform, specific file paths, etc.
        '''
        return self.analysis_settings
    
    def get_readable_name(self):
        '''\
        Returns a human readable name for the dataset (e.g. "State of the Union Addresses".)
        '''
        return self.dataset_metadata['readable_name']
    
    def get_description(self):
        '''\
        Returns a description of what the dataset contains, its importance, etc.
        '''
        return self.dataset_metadata['description']
    
    def get_creator(self):
        '''\
        Returns the name of the person who compiled the dataset, 
        or created a way to import the dataset.
        '''
        return self.dataset_metadata['creator']
    
    def get_source(self):
        '''\
        Returns the origination of the dataset (i.e. where the documents came from.)
        '''
        return self.dataset_metadata['source']
    
    def get_dataset_name(self):
        '''\
        Returns a name uniquely identifying this dataset on the
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
        Returns a DocumentIterator.
        '''
        return GenericDocumentIterator(self.documents_directory, self.subdocuments, self.recursive)

class GenericDocumentIterator:
    '''\
    Allows one to iterate through documents in a given document tree.
    '''
    
    def __init__(self, documents_directory, subdocuments, recursive):
        self.documents_directory = documents_directory
        self.subdocuments = subdocuments
        self.recursive = recursive
        
        self.list_of_documents = self.get_all_files(self.documents_directory)
        
    def get_all_files(self, file_path):
        '''\
        Gets a list of ALL the files in the dataset.
        '''
        all_files = []
        directories = []
        directories.append(file_path)
        
        while len(directories) > 0:
            file_path = directories.pop(0)
            all_files.extend(self.get_files(file_path))
            directories.extend(self.get_directories(file_path))
        return all_files
        
    def get_files(self, file_path):
        '''\
        Gets a list of all files in the given directory.
        '''
        files = [os.path.join(file_path, file_name) for file_name in os.listdir(file_path) \
                if self.is_valid_file(file_path, file_name)]
        return files
    
    def get_directories(self, file_path):
        '''\
        Gets a list of all directories in the given directory.
        '''
        dirs = [os.path.join(file_path, file_name) \
                for file_name in os.listdir(file_path) \
                if os.path.isdir(os.path.join(file_path, file_name))]
        return dirs
        
    def is_valid_file(self, file_path, file_name):
        '''\
        Helper function to detect hidden files and folders.
        '''
        is_dir = os.path.isfile(os.path.join(file_path, file_name))
        is_hidden_linux = file_name[0] != '.' and file_name[-1] != '~'
        return is_dir and is_hidden_linux
    
    def next(self):
        '''\
        Returns the next available document.
        '''
        for file_path in self.list_of_documents:
            try:
                document = GenericDocument(self.documents_directory, file_path)
                yield document
            except Exception as e:
                print('Error: Could not import %s' % file_path)
        raise StopIteration
        

class GenericDocument:
    '''\
    While the DataSetImportTask is an abstraction of an entire dataset 
    the Document class is an abstraction of a single document in that dataset.
    '''
    
    def __init__(self, root_doc_directory, document_path, subdocuments):
        self.root_doc_directory = root_doc_directory
        self.document_path = document_path
        self.subdocuments = subdocuments
        
        with open(self.document_path, 'r') as doc_file:
            s = doc_file.read()
            metadata, self.content = GenericTools.seperate_metadata_and_content(s)
            self.metadata = GenericTools.metadata_to_dict(metadata)
    
    def get_name(self):
        '''\
        Return a unique identifier for this document. Must only contain underscores or alphanumeric characters.
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
        Returns True if this document can be broken down into smaller
        chunks/documents; False if the document cannot be broken down or
        the user wants the entire document to be analyzed together.
        '''
        return self.subdocuments
    
    def __iter__(self):
        '''\
        Returns a Document iterator where each document is a portion of
        the original one.
        '''
        if self.subdocuments:
            return self
        else:
            raise Exception('Not able to split into subdocuments.')
    
    def next(self):
        '''\
        Returns a Document object representing a subdocument of this document.
        '''
        raise NotImplemented()


class AnalysisSettings:
    def __init__(self):
        self.number_of_topics = 100
        self.number_of_iterations = 100
        self.mallet_relative_file_path = 'tools/mallet/mallet'
    
    def set_number_of_iterations(self, iterations):
        self.number_of_iterations = iterations
        
    def set_number_of_topics(self, num_topics):
        self.number_of_topics = num_topics
    
    def get_number_of_iterations(self):
        return self.number_of_iterations
        
    def get_number_of_topics(self):
        return self.number_of_topics
    
    def get_mallet_file_path(self, topical_guide_root_dir):
        return os.path.join(topical_guide_root_dir, self.mallet_relative_file_path)
    
    def get_analysis_name(self):
        return 'lda%stopics' % self.number_of_topics
    
    def get_analysis_readable_name(self):
        return 'LDA %s Topics' % self.number_of_topics
        
    def get_analysis_description(self):
        return 'Mallet LDA with %s topics' % self.number_of_topics
    
    def get_mallet_configurations(self, topical_guide_dir, dataset_dir):
        config = dict()
        config['mallet'] = os.path.join(topical_guide_dir, 'tools/mallet/mallet')
        config['num_topics'] = self.number_of_topics
        config['mallet_input_file_name'] = 'mallet_input.txt'
        config['mallet_input'] = os.path.join(dataset_dir, config['mallet_input_file_name'])
        config['mallet_imported_data'] = os.path.join(dataset_dir, 'imported_data.mallet')
        analysis_name = 'lda%stopics' % self.number_of_topics
        mallet_out = os.path.join(dataset_dir, analysis_name)
        config['mallet_output_gz'] = mallet_out + '.outputstate.gz'
        config['mallet_output'] = mallet_out + '.outputstate'
        config['mallet_doctopics_output'] = mallet_out + '.doctopics'
        config['mallet_optimize_interval'] = 10
        config['num_iterations'] = self.number_of_iterations
        return config
    
    def get_topic_metrics(self):
        return ["token_count", "type_count", "document_entropy", "word_entropy"]
    
    # TODO most of these entities don't seem to exist... why?
    # the one that does is metadata/documents.json
    def get_metadata_filenames(self, metadata_dir):
        '''\
        Returns a dictionary of the metadata filenames.
        '''
        metadata_entities = ('datasets', 'documents', 'word_types', 'word_tokens', 'analysis', 'topics')
        metadata_filenames = {}
        for entity_type in metadata_entities:
            metadata_filenames[entity_type] = os.path.join(metadata_dir, entity_type)
        return metadata_filenames
    
    def get_pairwise_topic_metrics(self):
        return ['document_correlation']#, 'word_correlation']
    
    def get_pairwise_document_metrics(self):
        return ['word_correlation', 'topic_correlation']
    
    def get_topic_metric_args(self):
        return defaultdict(dict)

