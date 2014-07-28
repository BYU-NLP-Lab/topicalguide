from __future__ import print_function

import os
import codecs

from import_tool import basic_tools

class AbstractAnalysis(object):
    """
    The AbstractAnalysis allows the TopicalGuide import system to run 
    different analyses.
    """
    
    def __init__(self):
        """Initialize filters and stopwords."""
        pass

    def get_identifier(self):
        """Return a string that uniquely identifies this analysis."""
        raise NotImplementedError('get_identifier is not implemented')
    
    def get_stopwords(self):
        """Return a set of unicode stopwords the analysis used, or an empty list if none."""
        raise NotImplementedError('get_stopwords is not implemented')
    
    def get_metadata(self):
        """
        Return a dictionary where they keys are the metadata identifiers \
        and the values are the associated values for this analysis.
        Note that 'readable_name' and 'description' are special keys that are \
        used by the Topical Guide to neatly display basic information about your dataset.
        """
        raise NotImplementedError('get_metadata is not implemented')
    
    def get_working_directory(self):
        """
        Return the directory that contains temporary files used by this particular analysis.
        """
        raise NotImplementedError('get_working_directory is not implemented')
    
    def run_analysis(self, document_iterator):
        """Perform the analysis."""
        raise NotImplementedError('run_analysis is not implemented')
    
    def __iter__(self):
        """
        Return an iterator where next() will return a tuple like: 
        (document_name, word_token, topic_number).
        Note that document_name is the same name given by the 
        document_iterator in the prepare_analysis_input function; also, 
        all word tokens must be returned in the order they are in the 
        document.  Furthermore, the topic_number must be a cardinal 
        integer.
        """
        raise NotImplementedError('__iter__ is not implemented')

