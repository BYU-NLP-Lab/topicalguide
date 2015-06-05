from __future__ import division, print_function, unicode_literals
import io
import json
import math
import os
import re
import subprocess
from os.path import join, abspath
from import_tool import basic_tools
from import_tool.import_system_utilities import TOKEN_REGEX
from abstract_analysis import AbstractAnalysis

class StubCorpus:
    def __init__(self, documents):
        self._docs = documents

    def count(self):
        return len(self._docs)

    def __iter__(self):
        for ii in self._docs:
            yield ii

class StubDocument:
    def __init__(self, text):
        self._content = text

    def get_content(self):
        return self._content

class MalletItmAnalysis(AbstractAnalysis):
    """
    The AbstractAnalysis allows the TopicalGuide import system to run 
    different analyses.  All settings should be set before preparing or 
    running the analysis to avoid naming conflicts or inconsistencies.
    """
    
    def __init__(self, mallet_path, dataset_dir, base_dir, vocab_class, tree_class,
                 itm_class):
        """
        mallet_path -- the path to the mallet executable
        dataset_dir -- the directory the analysis can use to make its
                       own directory, this is done because the analysis
                       name may not be known until the run_analysis 
                       method is called; the analysis directory is 
                       used to store intermediate results
        """
        self.mallet_path = abspath(mallet_path)
        self.dataset_dir = abspath(dataset_dir)
        self.base_dir = abspath(base_dir)
        self.create_subdocuments_method = None
        self.vocab_class = vocab_class
        self.itm_class = itm_class
        self.tree_class = tree_class
        # Since words are mapped to numbers this doesn't need to be modified.
        mallet_token_regex=r"[\S]+"
        
        self.mallet_token_regex = mallet_token_regex
        self.python_token_regex_pattern = re.compile(r'[a-zA-z0-9_]', re.UNICODE)
        self.tree_hyperparameters_file = join(self.base_dir, 'tools', 'mallet_itm', 'input', 'tree_hyperparams')
        
        self.metadata = {}
        self.stopwords = {}
        self._excluded_words = {}
        
        self._set_names_and_description()
        self.token_regex = TOKEN_REGEX
        
        self.remove_singletons = False
        self.find_bigrams = False
        self.stem_words = False
    
    def _set_names_and_description(self):
        self.name = 'itm' + str(self.num_topics) + 'topics'
        self.readable_name = 'ITM with ' + str(self.num_topics) + ' Topics'
        self.description = 'ITM LDA with ' + str(self.num_topics) + ' topics.'
    
    @property
    def metadata_types(self):
        result = {}
        basic_tools.collect_types(result, self.metadata)
        return result
    
    @property
    def name(self):
        """Get the name."""
        return self._name
    @name.setter
    def name(self, name):
        """Set identifier and corresponding working directory, must be a string with valid directory characters."""
        self._name = name
        self.working_directory = abspath(join(self.dataset_dir, 'analyses/' + self.name))
    
    @property
    def readable_name(self):
        return self.metadata.setdefault('readable_name', self.name)
    @readable_name.setter
    def readable_name(self, readable_name):
        self.metadata['readable_name'] = readable_name
    
    @property
    def description(self):
        return self.metadata['description']
    @description.setter
    def description(self, description):
        self.metadata['description'] = description
    
    @property
    def optimize_interval(self):
        return self.metadata.setdefault('optimize_interval', 10)
    @optimize_interval.setter
    def optimize_interval(self, interval):
        self.metadata['optimize_interval'] = interval
    
    @property
    def num_topics(self):
        return self.metadata.setdefault('num_topics', 20)
    @num_topics.setter
    def num_topics(self, num_topics):
        self.metadata['num_topics'] = num_topics
        self._set_names_and_description()
    
    @property
    def num_iterations(self):
        return self.metadata.setdefault('num_iterations', 10)
    @num_iterations.setter
    def num_iterations(self, num_iterations):
        self.metadata['num_iterations'] = num_iterations
    
    @property
    def working_directory(self):
        return self._working_dir
    @working_directory.setter
    def working_directory(self, working_dir):
        """The working_dir is the directory the mallet input and output files will be stored in."""
        self._working_dir = abspath(working_dir)
        if not os.path.exists(self._working_dir):
            os.makedirs(self._working_dir)
        self.itm_vocab_file = join(self._working_dir, 'itm.voc')            
        self.stopwords_file = join(self._working_dir, 'stopwords.json')
        self.mallet_input_file = join(self._working_dir, 'mallet_input.txt')
        self.start_index_file = join(self._working_dir, 'start_index_file.json')
        self.subdoc_to_doc_map_file = join(self._working_dir, 'subdoc_to_doc_map.json')
        self.wordtype_to_number_file = join(self._working_dir, 'wordtype_to_number.json')
        self.number_to_wordtype_file = join(self._working_dir, 'number_to_wordtype.json')
        self.wordtype_file = join(self._working_dir, 'wordtypes.json')
        self.excluded_words_file = join(self._working_dir, 'excluded_words.json')
        self.raw_constraint_file = join(self._working_dir, 'init.cons')
        self.processed_constraint_file = join(self._working_dir, 'init.wn')
        self.tree_itm_library_path = join(self.base_dir, 'tools', 'mallet_itm', 'lib', '*')
        print(self.tree_itm_library_path)
        self.java_class_path = join(self.base_dir, 'tools', 'mallet_itm', 'class')
        
        self.mallet_imported_data_file = join(self._working_dir, 'imported_data.mallet')
        self.mallet_output_gz_file = join(self._working_dir, self.name + '.outputstate.gz')
        self.mallet_output_doctopics_file = join(self._working_dir, self.name + '.doctopics')
    
    @property
    def token_regex(self):
        return self._token_regex
    @token_regex.setter
    def token_regex(self, regex):
        self._token_regex = regex
        self._compiled_regex = re.compile(regex, re.UNICODE)
        self.metadata['token_regex'] = regex
    
    @property
    def excluded_words(self):
        if os.path.exists(self.excluded_words_file):
            with io.open(self.excluded_words_file, 'r', encoding='utf-8') as f:
                self._excluded_words = json.loads(f.read())
        return self._excluded_words
    @excluded_words.setter
    def excluded_words(self, words_dict):
        self._excluded_words = words_dict
    
    def tokenize(self, text):
        seq = []
        for match in self._compiled_regex.finditer(text):
            wordtype = match.group().lower()
            if wordtype not in self.stopwords:
                seq.append((wordtype, match.start()))
        return seq
    
    def add_stopwords_file(self, filepath):
        """Get stopwords."""
        with io.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for token, __ in self.tokenize(f.read()):
                self.stopwords[token] = True
    
    def set_create_subdocuments_method(self, method):
        """Set how the subdocuments should be created."""
        self.create_subdocuments_method = method
    
    def set_python_token_regex(self, token_regex):
        self.python_token_regex_pattern = re.compile(token_regex, re.UNICODE)
    
    def create_subdocuments(self, name, content):
        """
        Return a list of tuples like: (name, content).  Each tuple represents a subdocument and
        the concatenation of each subdocument's content should yield the original document (white 
        space being the exception).
        """
        if self.create_subdocuments_method:
            return self.create_subdocuments_method(str(name), content)
        else:
            return [(name, content)]
    
    def _cleanup(self, filename):
        if os.path.exists(filename):
            os.remove(filename)
    
    def _prepare_analysis_input(self, documents):
        """Combine every document into one large text file for processing with mallet."""
        subdoc_to_doc_map = {}
        wordtype_to_number = {}
        number_to_wordtype = []
        wordtypes = {}
        
        # prevent duplicating work
        if os.path.exists(self.wordtype_file):
            return
        
        try:
            # First find singletons
            if self.remove_singletons:
                word_type_count_threshold = max(1, int(math.log(documents.count(), 10)) - 2)
                temp_word_type_counts = {}
                for doc_index, doc in enumerate(documents):
                    tokens = self.tokenize(doc.get_content())
                    for token, token_start in tokens:
                        temp_word_type_counts[token] = temp_word_type_counts.setdefault(token, 0) + 1
                for word_type, count in temp_word_type_counts.iteritems(): # add singletons to stopword list
                    if count <= word_type_count_threshold:
                        self._excluded_words[word_type] = True
                with io.open(self.excluded_words_file, 'w', encoding='utf-8') as ex_f:
                    ex_f.write(unicode(json.dumps(self._excluded_words)))
            
            haltwords = dict(self.stopwords)
            haltwords.update(self._excluded_words)
            # Second find bigrams, iterate through documents and train.
            if self.find_bigrams:
                from import_tool.analysis.bigram_finder import BigramFinder
                bigram_finder = BigramFinder(stopwords=haltwords)
                for doc_index, doc in enumerate(documents):
                    bigram_finder.train(doc_index, self.tokenize(doc.get_content()))
                bigram_finder.print()
            
            # Third, we're going to stem words
            if self.stem_words:
                from import_tool.analysis.stemmer import Stemmer
                stemmer = Stemmer(self._working_dir, self.base_dir)
            
            # for each document tokenize and map tokens to numbers to avoid regex problems before passing data to Mallet
            with io.open(self.mallet_input_file, 'w', encoding='utf-8') as w:
                with io.open(self.start_index_file, 'w', encoding='utf-8') as w2:
                    count = 0
                    subcount = 0
                    for doc_index, doc in enumerate(documents):
                        doc_content = unicode(doc.get_content())
                        count += 1
                        subdocuments = self.create_subdocuments(doc_index, doc_content)
                        token_start_index_offset = 0 # needed to make sure the start index remains correct once the document is re-merged
                        for subdoc_name, subdoc_content in subdocuments:
                            if subcount > 0:
                                w2.write(u'\n')
                            subcount += 1
                            subdoc_to_doc_map[subdoc_name] = doc_index
                            tokens = self.tokenize(subdoc_content)
                            #~ print(tokens)
                            
                            if self.find_bigrams:
                                tokens = bigram_finder.combine(tokens, subdoc_content)
                            
                            token_numbers = []
                            token_start_indices = []
                            only_tokens = []
                            tokens_temp = []
                            for tok, tok_start in tokens:
                                only_tokens.append(tok)
                                tokens_temp.append([tok, tok_start + token_start_index_offset])
                            tokens = tokens_temp
                            tokens_temp = None
                            if self.stem_words:
                                stemmed_tokens = stemmer.stem(only_tokens)
                            else:
                                stemmed_tokens = only_tokens
                            for tup, tok_stem in zip(tokens, stemmed_tokens):
                                tok, tok_start = tup
                                wordtypes[tok] = True
                                wordtypes[tok_stem] = True
                                try:
                                    tok_num = wordtype_to_number[tok_stem]
                                except:
                                    tok_num = len(wordtype_to_number)
                                    number_to_wordtype.append(tok_stem)
                                    wordtype_to_number[tok_stem] = tok_num
                                token_numbers.append(unicode(tok_num))
                                token_start_indices.append([tok, tok_start])
                            text = u' '.join(token_numbers)
                            #~ print(text)
                            w.write(u'{0} all {1}\n'.format(subdoc_name, text))
                            w2.write(unicode(json.dumps(token_start_indices)))
                            token_start_index_offset += len(subdoc_content)
                            for tok, tok_start in tokens:
                                try:
                                    assert doc_content[tok_start:tok_start+len(tok)].lower() == tok.lower()
                                except:
                                    print(tok_start)
                                    print(len(tok))
                                    print('"'+doc_content[tok_start:tok_start+len(tok)].lower()+'"')
                                    print('"'+tok.lower()+'"')
                                    raise
                    if not count:
                        raise Exception('No files processed.')
            # record which subdocuments belong to which documents
            with io.open(self.subdoc_to_doc_map_file, 'w', encoding='utf-8') as w:
                w.write(unicode(json.dumps(subdoc_to_doc_map)))
            with io.open(self.wordtype_to_number_file, 'w', encoding='utf-8') as w:
                w.write(unicode(json.dumps(wordtype_to_number)))
            with io.open(self.number_to_wordtype_file, 'w', encoding='utf-8') as w:
                w.write(unicode(json.dumps(number_to_wordtype)))
            with io.open(self.wordtype_file, 'w', encoding='utf-8') as w:
                w.write(unicode(json.dumps(wordtypes)))
            self.wordtype_to_number = wordtype_to_number
        except: # cleanup
            self._cleanup(self.mallet_input_file)
            self._cleanup(self.subdoc_to_doc_map_file)
            self._cleanup(self.wordtype_to_number_file)
            self._cleanup(self.number_to_wordtype_file)
            self._cleanup(self.wordtype_file)
            self._cleanup(self.excluded_words_file)
            raise
    
    def get_java_class_path(self):
        return self.java_class_path + ':'+self.tree_itm_library_path
    
    def set_constraints(self, merge_links, split_links):
        # TODO: This overwrites any older constraints
        # Possible issue: this could have a vocab mismatch depending
        # on import pipeline, needs to be tested
        
        with io.open(self.raw_constraint_file, 'w', encoding='utf-8') as o:
            print('constraints')
            print(merge_links)
            print(self.wordtype_to_number)
            for ii in merge_links:
                print(ii)
                wordtype_indices = [unicode(self.wordtype_to_number[wt]) for wt in ii]
                o.write("MERGE_\t%s" % "\t".join(wordtype_indices))
                print(wordtype_indices)
            #~ for jj in split_links:
                #~ o.write("SPLIT_\t%s" % "\t".join(ii))

        # Generate the protocol buffer with the real version
        cmd = ['java', '-cp', self.get_java_class_path(), self.tree_class, '--vocab',
               self.itm_vocab_file, '--constraint',
               self.raw_constraint_file, '--tree',
               self.processed_constraint_file]
        print(" ".join(cmd))
        try:
            subprocess.check_call(cmd)
        except:
            self._cleanup(self.processed_constraint_file)
            raise
    
    def prepare_analysis(self, documents):
        """Preprocess documents. Import into mallet format. Compile the vocab."""
        if documents.count() == 0:
            raise Exception('No documents to perform analysis on.')
        
        self._prepare_analysis_input(documents)
        
        with io.open(self.stopwords_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.stopwords.keys()))
        
        if not os.path.exists(self.mallet_imported_data_file):
            cmd = [self.mallet_path, 'import-file', 
                   '--input', self.mallet_input_file, 
                   '--output', self.mallet_imported_data_file, 
                   '--token-regex', self.mallet_token_regex, 
                   '--keep-sequence', 
                   '--remove-stopwords']
            print(" ".join(cmd))
            
            try:
                subprocess.check_call(cmd)
            except: # cleanup
                self._cleanup(self.mallet_imported_data_file)
                raise
        
        if not os.path.exists(self.itm_vocab_file):
            cmd = ['java', '-cp', self.get_java_class_path(), self.vocab_class, '--input', self.mallet_imported_data_file, '--vocab', self.itm_vocab_file, '--word-length', '0', '--freq-thresh', '0']
            print(' '.join(cmd))
            try:
                subprocess.check_call(cmd)
            except:
                self._cleanup(self.itm_vocab_file)
    
    def run_analysis(self):
        """Run ITM."""
        # train topics
        if not (os.path.exists(self.mallet_output_gz_file) and \
                os.path.exists(self.mallet_output_doctopics_file)):
            cmd = ['java', '-cp', self.get_java_class_path(), self.itm_class, '--input',
                   self.mallet_imported_data_file, '--tree-hyperparameters',
                   self.tree_hyperparameters_file, '--vocab', self.itm_vocab_file,
                   '--num-topics', '%s' % str(self.num_topics),'--num-iterations',
                    '%s' % str(self.num_iterations), '--output-dir',
                     self.mallet_output_gz_file, '--tree', self.processed_constraint_file]
            print(" ".join(cmd))
#            cmd = [self.mallet_path, 'train-topics', 
#                   '--input', self.mallet_imported_data_file,
#                   '--optimize-interval', str(self.optimize_interval),
#                   
#                   
#                   ]
            try:
                subprocess.check_call(cmd)
            except: # cleanup
                self._cleanup(self.mallet_output_gz_file)
                self._cleanup(self.mallet_output_doctopics_file)
                raise
    
    def get_vocab_iterator(self):
        result = []
        with io.open(self.wordtype_file, 'r', encoding='utf-8') as f:
            result = json.loads(f.read())
        return result
    
    def get_token_iterator(self):
        return self
    
    def __iter__(self):
        """
        Return an iterator where next() will return a tuple like: 
        (document_name, word_token, topic_number).
        Note that document_name is the same name given by the 
        document_iterator in the _prepare_analysis_input function; also, 
        all word tokens must be returned in the order they are in the 
        document.  Furthermore, the topic_number must be a cardinal 
        integer.
        """
        self.mallet_output_file = join(self._working_dir, self.name + '.outputstate')
        
        # decompress mallet output
        if not os.path.exists(self.mallet_output_file):
            cmd = 'gunzip -c %s > %s' % (self.mallet_output_gz_file, self.mallet_output_file)
            try:
                subprocess.check_call(cmd, shell=True)
            except: # cleanup
                if os.path.exists(self.mallet_output_file):
                    os.remove(self.mallet_output_file)
                raise
        
        # get subdocument to document map
        self.subdoc_to_doc_map = {}
        with io.open(self.subdoc_to_doc_map_file, 'r', encoding='utf-8') as f:
            self.subdoc_to_doc_map = json.loads(f.read())
        self.number_to_wordtype = []
        with io.open(self.number_to_wordtype_file, 'r', encoding='utf-8') as f:
            self.number_to_wordtype = json.loads(f.read())
        
        return self.next() # create a generator
    
    def next(self):
        """Return the next tuple."""
        with io.open(self.start_index_file, 'r', encoding='utf-8') as f_index:
            with io.open(self.mallet_output_file, 'r', encoding='utf-8') as f:
                start_indices = json.loads(f_index.readline())
                si_line_num = 1
                subdoc_index = 0
                
                try:
                    line_num = 0
                    for line in f:
                        line_num += 1
                        # avoid comments
                        if line[0] == '#':
                            continue
                        subdoc_number, subdoc_name, token_pos, word_type_num, token_number, topic_num = line.split()
                        doc_index = self.subdoc_to_doc_map[subdoc_name]
                        while subdoc_index != int(subdoc_number):
                            subdoc_index += 1
                            start_indices = json.loads(f_index.readline())
                            si_line_num += 1
                            assert int(token_pos) == 0
                        tok_index = int(token_pos)
                        token = self.number_to_wordtype[int(token_number)]
                        start_index = start_indices[tok_index]
                        
                        yield (doc_index, start_index[1], start_index[0], token, (int(topic_num),))
                except:
                    print(subdoc_number, subdoc_name, token_pos, word_type_num, token_number, topic_num)
                    print(doc_index, subdoc_index, tok_index, len(start_indices), line_num, si_line_num)
                    print(len(self.number_to_wordtype))
                    print(len(start_indices))
                    raise
        raise StopIteration
    
    def get_hierarchy_iterator(self):
        return []

def main():
    corpus = [
        StubDocument("dog dog cat cat cat dog cat dog bark"), 
        StubDocument("tree elm oak oak elm elm tree tree bark"),
        StubDocument("tree elm dog oak elm elm tree tree bark"),
    ]
    corpus = StubCorpus(corpus)

    mallet_location = "tools/mallet_itm/tree-TM/bin/mallet"
    vocab_location = "cc.mallet.topics.tui.GenerateVocab"
    tree_location = "cc.mallet.topics.tui.GenerateTree"
    itm_location = "cc.mallet.topics.tui.Vectors2TreeTopics"

    itm = MalletItmAnalysis(mallet_location, "./working/datasets/temp",
                            ".", vocab_location, tree_location,
                            itm_location)
    itm.prepare_analysis(corpus)
    itm.set_constraints([["dog", "bark"]], [["dog", "elm"]])
    itm.run_analysis()

if __name__ == "__main__":
    main()
