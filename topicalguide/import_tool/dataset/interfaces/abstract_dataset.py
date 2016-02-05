from __future__ import division, print_function


class AbstractDataset(object):
    """
    The AbstractDataset defines an interface into the TopicalGuide 
    import system's import_dataset method. This allows different 
    datasets to be run without duplicating the import code.
    
    REMEMBER: Use the @property decorator if properties need to be 
    generated.
    
    The properties required to interface with the import system are:
    name -- the name to uniquely identify this dataset
    metadata -- dict with dataset metadata, description and
                readable_name are special entries that will be displayed
                to the user
    metadata_types -- a dict mapping the metadata keys to their
                      datatypes (e.g. 'int', 'float', 'text', 'datetime').
    document_metadata_types -- a dict mapping document metadata keys to
                               their datatypes
    
    The required functions to interface with the import system are:
    __iter__
    __len__
    """
    def __init__(self):
        self.name = ''
        self.metadata_types = {}
        self.metadata = {}
        self.document_metadata_types = {}
    
    def __iter__(self):
        """Return an AbstractDocument iterator that iterates over 
        documents in alphabetical order.
        """
        raise NotImplementedError('__iter__ is not implemented')
    
    def __len__(self):
        """Return the number of documents to be imported."""
        raise NotImplementedError('__len__ is not implemented')


class AbstractDocument(object):
    """
    While the AbstractDataset is an abstraction of an entire dataset 
    the AbstractDocument class is an abstraction of a single document 
    in that dataset.
    
    The properties required to interface with the import system are:
    name -- the name to uniquely identify this document
    source -- a url identifying the original source of the document,
              a None value is acceptable if the source is unavailable
    content -- unicode string of the document's text
    metadata -- a dict with metadata
    """
    def __init__(self):
        self.name = ''
        self.source = None
        self.content = ''
        self.metadata = {}
