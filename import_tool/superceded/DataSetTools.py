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


#A single object encapsulating every item necessary to import
#a dataset.  To create a customized Project class, just inherit from 
#this class and replace functions as needed.
class Project:
    """/
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




            
            





