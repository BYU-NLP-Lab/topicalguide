from __future__ import print_function

class AbstractDataset(object):
    '''\
    The AbstractDataset is an abstraction that allows the import process \
    to interact with the dataset in a standardized manner. \
    This allows for flexibility in what datasets \
    can be imported and how they are imported. 
    To create a class that imports \
    data from a dataset with a specialized format or structure, extend this \
    class and override functions as necessary.
    '''
    
    def get_analysis_settings(self):
        '''\
        Returns an AnalysisSettings object that tracks which analysis' \
        to perform, mallet file paths, etc.
        '''
        raise NotImplementedError('get_analysis_settings is not implemented')
    
    def get_identifier(self):
        '''\
        Returns a string that uniquely identifies this dataset on the \
        Topical Guide server.
        '''
        raise NotImplementedError('get_dataset_identifier is not implemented')
    
    def get_readable_name(self):
        '''\
        Returns a string that identifies the dataset and is formatted \
        to be read by a human.
        '''
        raise NotImplementedError('get_readable_name is not implemented')
    
    def get_description(self):
        '''\
        Returns a description of the dataset.
        '''
        raise NotImplementedError('get_description is not implemented')
    
    def get_metadata(self):
        '''\
        Returns a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this dataset.
        Note that 'readable_name' and 'description' are special keys that are \
        required by the Topical Guide to neatly display basic information about your dataset.
        '''
        raise NotImplementedError('get_dataset_metadata is not implemented')
    
    def __iter__(self):
        '''\
        Returns an AbstractDocument iterator.
        '''
        raise NotImplementedError('__iter__ is not implemented')


class AbstractDocument(object):
    '''\
    While the AbstractDataset is an abstraction of an entire dataset \
    the AbstractDocument class is an abstraction of a single document in that dataset.
    '''
    
    def get_identifier(self):
        '''\
        Return a unique identifier for this document in relation to its dataset.
        Must only contain underscores, dashes, periods, or alphanumeric characters.
        '''
        raise NotImplementedError('get_name is not implemented')
    
    def get_uri(self):
        '''\
        Returns the document's uri.
        '''
        raise NotImplementedError('get_document_uri is not implemented')
    
    def get_metadata(self):
        '''\
        Returns a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        '''
        raise NotImplementedError('get_metadata is not implemented')
    
    def get_content(self):
        '''\
        Returns the raw text of the document.
        '''
        raise NotImplementedError('get_content is not implemented')
    
    def has_subdocuments(self):
        '''\
        Returns True if this document can be broken down into smaller
        chunks/documents; False if the document cannot be broken down or
        the user wants the entire document to be analyzed together.
        Must implement the __iter__ function if True is returned.
        '''
        raise NotImplementedError('has_subdocuments is not implemented')
    
    def __iter__(self):
        '''\
        Returns an AbstractDocument iterator where each document is a portion of
        the original one.
        '''
        raise NotImplementedError('__iter__ is not implemented')

