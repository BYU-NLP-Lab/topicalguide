from __future__ import division, print_function, unicode_literals


class AbstractTokenizer(object):
    def __init__(self):
        pass

    def _tokenize(self, text):
        """Internal method used by find_singletons and find_bigrams.
        Split the text into tokens. This function must give the exact same 
        token sequence if the input text is the same.
        text -- Unicode string.
        Return list of tokens.
        """
        raise NotImplementedError('tokenize is not implemented')


