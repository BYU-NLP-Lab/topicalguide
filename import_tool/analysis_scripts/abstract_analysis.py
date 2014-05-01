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
    
    def get_readable_name(self):
        """Return a string that contains a human readable name for this analysis."""
        raise NotImplementedError('get_readable_name is not implemented')
        
    def get_description(self):
        """Return a string describing this analysis."""
        raise NotImplementedError('get_description is not implemented')
    
    def get_stopwords(self):
        """Return a list of unicode stopwords the analysis used, or an empty list if none."""
        raise NotImplementedError('get_stopwords is not implemented')
    
    def prepare_analysis_input(self, document_iterator):
        """
        Do any preping needed for this analysis; document_iterator must 
        iterator over documents returning a tuple like: 
        (document_name, document_text.)
        """
        raise NotImplementedError('prepare_analysis_input is not implemented')
    
    def run_analysis(self):
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

