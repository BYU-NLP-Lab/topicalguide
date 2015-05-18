from __future__ import division, print_function


class AbstractDataset(object):
    """
    The AbstractDataset defines an interface into the TopicalGuide 
    import system's import_dataset method. This allows different 
    datasets to be run without duplicating the import code.
    
    REMEMBER: Use the @property decorator if properties need to be 
    generated.
    
    DATA TYPES: See the MetadataType class for a complete listing of supported
                datatypes.
    
    The properties required to interface with the import system are:
    name -- the name to uniquely identify this dataset
    
    metadata -- dict with dataset metadata, description and
                readable_name are special entries that will be displayed
                to the user
                
    metadata_types -- a dict mappting the metadata key to the required type of 
                      the value; these will be checked and an error thrown 
                      if they don't match what is given the import system; 
                      if empty the types will automatically be determined
                      
    document_metadata_types -- a dict listing the required types for certain 
                               metadata attributes
                               
    document_required_metadata -- a set (or dict) specifying metadata
                                  keys that must be present in every
                                  document
    document_metadata_ordinals -- a dict mapping the metadata key to a list
                                  of lists of strings; note that there can
                                  be multiple strings that map to a single 
                                  number (e.g. "January" and "Jan" map to 0)
    
    NOTE: The import system will automatically try to determine the metadata
          types of the metadata, because of this there are two passes through
          the document objects. This is done to ensure the integrity of the
          document metadata type. If the metadata types varied from document
          to document on the same metadata key, then the views become more
          complicated (introducing a number of edge cases).
    
    RECOMMENDATION: If your documents are being pulled from the web, cache them
                    somewhere to make the import process faster.
    
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
