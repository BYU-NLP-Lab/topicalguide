from __future__ import print_function

class AbstractDataset(object):
    """
    The AbstractDataset is an abstraction that allows the import process \
    to interact with the dataset in a standardized manner. \
    This allows for flexibility in what datasets \
    can be imported and how they are imported. 
    To create a class that imports \
    data from a dataset with a specialized format or structure, extend this \
    class and override functions as necessary.
    """
    
    readable_name = "You should override this item."
    description = "You should override this item."
    
    def get_identifier(self):
        """
        Return a string that uniquely identifies this dataset on the \
        Topical Guide server.
        """
        raise NotImplementedError('get_identifier is not implemented')
    
    def get_metadata(self):
        """
        Return a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this dataset.
        Note that 'readable_name' and 'description' are special keys that are \
        required by the Topical Guide to neatly display basic information about your dataset.
        """
        raise NotImplementedError('get_metadata is not implemented')
    
    def __iter__(self):
        """Return an AbstractDocument iterator."""
        raise NotImplementedError('__iter__ is not implemented')
    
    def __len__(self):
        """Return the number of documents to be imported."""
        raise NotImplementedError('__len__ is not implemented')


class AbstractDocument(object):
    """
    While the AbstractDataset is an abstraction of an entire dataset \
    the AbstractDocument class is an abstraction of a single document in that dataset.
    """
    
    def get_identifier(self):
        """
        Return a unique identifier for this document in relation to its dataset.
        Must only contain underscores, dashes, periods, or alphanumeric characters.
        """
        raise NotImplementedError('get_identifier is not implemented')
    
    def get_uri(self):
        """Return the document's uri."""
        raise NotImplementedError('get_uri is not implemented')
    
    def get_metadata(self):
        """
        Return a dictionary where the keys are the metadata identifiers and
        the values are the document associated values 
        (e.g. "author": "Isaac Asimov", "year": 1952, etc.)
        """
        raise NotImplementedError('get_metadata is not implemented')
    
    def get_content(self):
        """Return a utf-8 string of the document."""
        raise NotImplementedError('get_content is not implemented')

