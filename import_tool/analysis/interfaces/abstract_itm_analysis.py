from __future__ import division, print_function, unicode_literals
from abstract_analysis import AbstractAnalysis


class AbstractITMAnalysis(AbstractAnalysis):
    
    def __init__(self):
        """Initialize required fields."""
        super(AbstractAnalysis, self).__init__()
    
    def resume(self, verbose=False):
        raise NotImplementedError('resume is not implemented')
    
    def remove_words(self, words):
        raise NotImplementedError('remove_words is not implemented')
    
    def set_word_constraints(self, merge_words, split_words):
        raise NotImplementedError('set_word_constraints is not implemented')
    
    def get_word_constraints(self):
        raise NotImplementedError('get_word_constraints is not implemented')
