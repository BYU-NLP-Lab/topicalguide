from __future__ import print_function

import os
from collections import defaultdict

# TODO fill in documentation

class AnalysisSettings:
    def __init__(self):
        self.number_of_topics = 50
        self.number_of_iterations = 100
        self.mallet_relative_file_path = 'tools/mallet/mallet'
    
    def set_number_of_iterations(self, iterations):
        self.number_of_iterations = iterations
        
    def set_number_of_topics(self, num_topics):
        self.number_of_topics = num_topics
    
    def get_number_of_iterations(self):
        return self.number_of_iterations
        
    def get_number_of_topics(self):
        return self.number_of_topics
    
    def get_mallet_file_path(self, topical_guide_root_dir):
        return os.path.join(topical_guide_root_dir, self.mallet_relative_file_path)
    
    def get_analysis_name(self):
        return 'lda%stopics' % self.number_of_topics
    
    def get_analysis_readable_name(self):
        return 'LDA %s Topics' % self.number_of_topics
        
    def get_analysis_description(self):
        return 'Mallet LDA with %s topics' % self.number_of_topics
    
    def get_mallet_configurations(self, topical_guide_dir, dataset_dir):
        config = dict()
        config['mallet'] = os.path.join(topical_guide_dir, 'tools/mallet/mallet')
        config['num_topics'] = self.number_of_topics
        config['mallet_input_file_name'] = 'mallet_input.txt'
        config['mallet_input'] = os.path.join(dataset_dir, config['mallet_input_file_name'])
        config['mallet_imported_data'] = os.path.join(dataset_dir, 'imported_data.mallet')
        analysis_name = 'lda%stopics' % self.number_of_topics
        mallet_out = os.path.join(dataset_dir, analysis_name)
        config['mallet_output_gz'] = mallet_out + '.outputstate.gz'
        config['mallet_output'] = mallet_out + '.outputstate'
        config['mallet_doctopics_output'] = mallet_out + '.doctopics'
        config['mallet_optimize_interval'] = 10
        config['num_iterations'] = self.number_of_iterations
        return config
    
    def get_topic_metrics(self):
        return ["token_count", "type_count", "document_entropy", "word_entropy"]
    
    # TODO most of these entities don't seem to exist... why?
    # the one that does exist is metadata/documents.json
    def get_metadata_filenames(self, metadata_dir):
        '''\
        Returns a dictionary of the metadata filenames.
        '''
        metadata_entities = ('datasets', 'documents', 'word_types', 'word_tokens', 'analysis', 'topics')
        metadata_filenames = {}
        for entity_type in metadata_entities:
            metadata_filenames[entity_type] = os.path.join(metadata_dir, entity_type) + '.json'
        return metadata_filenames
    
    def get_pairwise_topic_metrics(self):
        return ['document_correlation', 'word_correlation']
    
    def get_pairwise_document_metrics(self):
        return ['topic_correlation']
    
    def get_topic_metric_args(self):
        return defaultdict(dict)



