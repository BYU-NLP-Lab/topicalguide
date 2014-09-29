from __future__ import print_function

import os
import json
import codecs
import subprocess
from os.path import join, abspath

from import_tool import basic_tools
from abstract_analysis import AbstractAnalysis
from topic_modeling.tools import TimeLongThing


class MALLETAnalysis(AbstractAnalysis):
    """
    The AbstractAnalysis allows the TopicalGuide import system to run 
    different analyses.  All settings should be set before preparing or 
    running the analysis to avoid naming conflicts or inconsistencies.
    """
    
    def __init__(self, topical_guide_root_dir, dataset_dir, number_of_topics=50, number_of_iterations=100, token_regex=r'[\p{L}_]+'):
        """
        The dataset_dir is just in case the working_directory path is not set.
        The token regex must be MALLET compatible.
        """
        self.filters = [] # a list of functions that take text as an argument and return text
        self.stopwords = set()
        self.create_subdocuments_method = None
        self.optimize_interval = 10
        self.num_topics = number_of_topics
        self.num_iterations = number_of_iterations
        
        self.dataset_dir = dataset_dir
        self.mallet_path = abspath(join(topical_guide_root_dir, 'tools/mallet/mallet'))
        
        self.token_regex = token_regex
        
        self.metadata = {}
        
        # determined when prepare_analysis_input is called if not specified sooner
        self.identifier = 'lda' + str(self.num_topics) + 'topics'
        self.set_working_directory(abspath(join(self.dataset_dir, 'analyses/' + self.identifier)))
        self.readable_name = 'LDA with ' + str(self.num_topics) + ' Topics'
        self.metadata['readable_name'] = self.readable_name
        self.description = 'Mallet LDA with ' + str(self.num_topics) + ' topics.'
        self.metadata['description'] = self.description
    
    def set_identifier(self, identifier):
        """Set identifier and corresponding working directory, must be a string with valid directory characters."""
        self.identifier = identifier
        self.set_working_directory(abspath(join(self.dataset_dir, 'analyses/' + self.identifier)))
    
    def set_readable_name(self, readable_name):
        """Set identifier, must be a string with valid directory characters."""
        self.readable_name = readable_name
        self.metadata['readable_name'] = readable_name
    
    def set_description(self, description):
        """Set identifier, must be a string with valid directory characters."""
        self.description = description
        self.metadata['description'] = description
    
    def set_working_directory(self, working_dir):
        """The working_dir is the directory the mallet input and output files will be stored in."""
        self.working_dir = abspath(working_dir)
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
    
    def get_working_directory(self):
        return self.working_dir
    
    def get_identifier(self):
        """Return a string that uniquely identifies this analysis."""
        return self.identifier
    
    def get_readable_name(self):
        """Return a string that contains a human readable name for this analysis."""
        return self.readable_name
        
    def get_description(self):
        """Return a string describing this analysis."""
        return self.description
        
    def get_stopwords(self):
        """Return stopwords."""
        return self.stopwords
    
    def get_metadata(self):
        return self.metadata
    
    # Do not add any filters that replace or add anything to the text as it may make it so your
    # tokens don't line up.
    def add_filters(self, filters):
        """
        Take a list of strings and add the appropriate filters and 
        stopwords.  All filters are functions that take a string as 
        an argument and return a string.
        Supported filter identifiers are:
        remove-html-tags
        stopwords:"<file name>"
        
        Note that any filter that replaces or adds text may make importing the token to topic relationships break.
        """
        for f in filters:
            if f == 'remove-html-tags':
                self.filters.append(basic_tools.remove_html_tags)
            elif f.startswith('stopwords'):
                file_path = f.split(':', 1)[1][1:-1]
                with codecs.open(file_path, 'r', 'utf-8') as word_file:
                    words = word_file.readlines()
                    words = [word.strip() for word in words]
                    self.add_stopwords(words)
    
    def add_stopwords(self, stopwords):
        """Add a list of strings to the stopwords."""
        for word in stopwords:
            self.stopwords.add(word)
    
    def filter_text(self, text):
        """Take a bit of text and run it through all available filters."""
        for text_filter in self.filters:
            text = text_filter(text)
        return text
    
    def set_create_subdocuments_method(self, method):
        """Set how the subdocuments should be created."""
        self.create_subdocuments_method = method
    
    def create_subdocuments(self, name, content):
        """
        Return a list of tuples like: (name, content).  Each tuple represents a subdocument and
        the concatenation of each subdocument's content should yield the original document (white 
        space being the exception.)
        """
        if self.create_subdocuments_method:
            return self.create_subdocuments_method(name, content)
        else:
            return [(name, content)]
    
    def prepare_analysis_input(self, document_iterator):
        """Combine every document into one large text file for processing with mallet."""
        
        self.mallet_input_file = join(self.working_dir, 'mallet_input.txt')
        self.subdoc_to_doc_map_file = join(self.working_dir, 'subdoc_to_doc_map.json')
        subdoc_to_doc_map = {}
        
        # prevent duplicating work
        if os.path.exists(self.mallet_input_file) and os.path.exists(self.subdoc_to_doc_map_file):
            return
        
        try:
            # for each document, strip out '\n' and '\r' and put  onto one line in the mallet input file
            with codecs.open(self.mallet_input_file, 'w', 'utf-8') as w:
                count = 0
                for doc_name, doc_content in document_iterator:
                    count += 1
                    subdocuments = self.create_subdocuments(doc_name, doc_content)
                    for subdoc_name, subdoc_content in subdocuments:
                        subdoc_to_doc_map[subdoc_name] = doc_name
                        text = subdoc_content.replace(u'\n', u' ').replace(u'\r', u' ')
                        w.write(u'{0} all {1}\n'.format(subdoc_name, self.filter_text(text)))
                if not count:
                    raise Exception('No files processed.')
            # record which subdocuments belong to which documents
            with codecs.open(self.subdoc_to_doc_map_file, 'w', 'utf-8') as w:
                w.write(json.dumps(subdoc_to_doc_map))
        except: # cleanup
            if os.path.exists(self.mallet_input_file):
                os.remove(self.mallet_input_file)
            if os.path.exists(self.subdoc_to_doc_map_file):
                os.remove(self.subdoc_to_doc_map_file)
            raise
    
    def run_analysis(self, document_iterator):
        """Run MALLET."""
        self.prepare_analysis_input(document_iterator)
        
        self.stopwords_file = join(self.working_dir, 'stopwords.txt')
        with codecs.open(self.stopwords_file, 'w', 'utf-8') as f:
            f.write('\n'.join(self.stopwords))
        
        self.mallet_imported_data_file = join(self.working_dir, 'imported_data.mallet')
        self.mallet_output_gz_file = join(self.working_dir, self.identifier + '.outputstate.gz')
        self.mallet_output_doctopics_file = join(self.working_dir, self.identifier + '.doctopics')
        
        if not os.path.exists(self.mallet_imported_data_file):
            cmd = [self.mallet_path, 'import-file', 
                   '--input', self.mallet_input_file, 
                   '--output', self.mallet_imported_data_file, 
                   '--keep-sequence', 
                   '--set-source-by-name',
                   '--remove-stopwords']
            
            if self.stopwords:
                cmd.append(' --extra-stopwords ')
                cmd.append(self.stopwords_file)
            if self.token_regex:
                cmd.append(' --token-regex ')
                cmd.append(self.token_regex)
            
            try:
                subprocess.check_call(cmd)
            except: # cleanup
                if os.path.exists(self.mallet_imported_data_file):
                    os.remove(self.mallet_imported_data_file)
                raise
        
        # train topics
        if not (os.path.exists(self.mallet_output_gz_file) and os.path.exists(self.mallet_output_doctopics_file)):
            cmd = [self.mallet_path, 'train-topics', 
                   '--input', self.mallet_imported_data_file,
                   '--optimize-interval', str(self.optimize_interval),
                   '--num-iterations', '%s' % str(self.num_iterations), 
                   '--num-topics', '%s' % str(self.num_topics),
                   '--output-state', self.mallet_output_gz_file, 
                   '--output-doc-topics', self.mallet_output_doctopics_file]
            try:
                subprocess.check_call(cmd)
            except: # cleanup
                if os.path.exists(self.mallet_output_gz_file):
                    os.remove(self.mallet_output_gz_file)
                if os.path.exists(self.mallet_output_doctopics_file):
                    os.remove(self.mallet_output_doctopics_file)
                raise
    
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
        self.mallet_output_file = join(self.working_dir, self.identifier + '.outputstate')
        
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
        with codecs.open(self.subdoc_to_doc_map_file, 'r', 'utf-8') as f:
            self.subdoc_to_doc_map = json.loads(f.read())
        
        return self.next() # create a generator
    
    def next(self):
        """Return the next tuple."""
        with codecs.open(self.mallet_output_file, 'r', 'utf-8') as f:
            lines = list(f)
            timer = TimeLongThing(len(lines))
            for line in lines:
                timer.inc()
                # avoid comments
                if line[0] == '#':
                    continue
                subdoc_number, subdoc_name, token_pos, word_type, word_token, topic_num = line.split()
                yield (self.subdoc_to_doc_map[subdoc_name], word_token, int(topic_num))
        raise StopIteration
