
import random
from .abstract_analysis import AbstractAnalysis


class RandomAnalysis(AbstractAnalysis):
    def __init__(self, mallet_path, dataset_dir, base_dir):
        """Initialize required fields."""
        self.name = ''
        self.metadata = {}
        self.metadata_types = {}
        self.stopwords = {}
        self.excluded_words = {}
        self.vocab = {}
        
        self.find_bigrams = False
        self.remove_singletons = False
        self.stem_words = False
        self.seed = 0
        self.text_length = 5
        self.number_of_topics = 20
    
    def tokenize(self, content):
        length = len(content)
        index = 0
        result = []
        while index < length:
            token = content[index: index + self.text_length]
            result.append((index, token))
            self.vocab[token] = True
            index += self.text_length
        return result
    
    def run_analysis(self, document_iterator):
        """Perform the analysis.
        document_iterator -- an iterator over documents, the order 
                             iterated over indicates the document's index
        Each document has the methods get_content, the document text; and get_metadata, the associated metadata for the document.
        document_metadata_types -- the type of the metadata fields
        Return nothing.
        """
        for doc in document_iterator:
            content = doc.get_content()
            tokens = self.tokenize(content)
        self.docs = document_iterator
    
    def get_vocab_iterator(self):
        """Return an iterator over the vocabulary."""
        return self.vocab
    
    def get_token_iterator(self):
        """Return an iterator where each element is like: 
        (document_index, start_index, token, token_abstraction, topic_number_list).
        document_index -- the same index as given by the document_iterator
        start_index -- the location, as a character offset, of the word in the original text
        token -- unicode string of the token
        token_abstraction -- unicode string representing a type, e.g. the stem of the word
        topic_number_list -- a list of topic numbers
        Note that all 'token_index's must be returned in order.
        """
        random.seed(self.seed)
        for doc in self.docs:
            content = doc.get_content()
            tokens = self.tokenize(content)
            for index, token in tokens:
                yield (doc.index, index, token, token, (random.randint(0, self.number_of_topics-1),))
    
    def get_hierarchy_iterator(self):
        """Return an iterator specifying the heirarchy.
        Each item is of the format (parent_topic, child_topic). 
        Return empty iterator if each topic has no parents."""
        return []

