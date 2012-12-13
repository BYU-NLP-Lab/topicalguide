#!/usr/bin/env python
# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

import os
import imp
from os.path import join
from collections import defaultdict
from helper_scripts.name_schemes.top_n import TopNTopicNamer

from topic_modeling import settings
from import_tool.local_settings import LOCAL_DIR, build

class Config(dict):
    overrides = {}

    def __getitem__(self, key):
        value = super(Config, self).__getitem__(key)
        if callable(value):
            value = value(self)
            self[key] = value
            return value
        else:
            return value

    def default(self, key, value):
        if key not in self: self[key] = value

    def required(self, key):
        if key not in self: raise Exception("Configuration key '%s' is required")

def get_buildscript(build):
    path = join(os.path.dirname(__file__), '../build')
    fname = join(path, '{0}.py'.format(build))
    fobj = open(fname)
    return imp.load_module(build, fobj, fname, ('.py', 'r', imp.PY_SOURCE))
    # return __import__(build, 'build/')

def create_config(build_script):
    '''The configuration dictionary'''
    config = Config()
    '''A shorthand alias for the config dictionary'''
    c = config
    build_script.update_config(c)

    if 'initialize_config' in locals(): locals()['initialize_config'](c)

    c.required('dataset_name')
    c.default('dataset_readable_name', c['dataset_name'])
    c.default('dataset_description', '')

    c.default('stopwords_file', '/aml/data/stopwords/english.txt')
    c.default('analysis_name', lambda c: "lda%stopics" % c['num_topics'])
    c.default('analysis_readable_name', lambda c: "LDA %s Topics" % c['num_topics'])
    c.default('analysis_description', lambda c: "Mallet LDA with %s topics" % c['num_topics'])
    c.default('base_dir', LOCAL_DIR)
    c.default('raw_data_base_dir', join(os.curdir, "raw-data"))
    c.default('raw_data_dir', join(c['raw_data_base_dir'], c['dataset_name']))
    c.default('datasets_dir', join(c['base_dir'], "datasets"))
    c.default('dataset_dir', join(c['datasets_dir'], c['dataset_name']))
    c.default('files_dir', join(c['dataset_dir'], "files"))
    if not os.path.exists(c['files_dir']):
        os.makedirs(c['files_dir'])
    c.default('token_regex', r'[A-Za-z]+')

    # Mallet
    c.default('mallet', join(os.curdir, "tools/mallet/mallet"))
    c.default('num_topics', 50)
    c.default('mallet_input_file_name', "mallet_input.txt")
    c.default('mallet_input', join(c['dataset_dir'], c['mallet_input_file_name']))
    c.default('mallet_imported_data', join(c['dataset_dir'], "imported_data.mallet"))
    mallet_out = join(c['dataset_dir'], c['analysis_name'])
    c.default('mallet_output_gz', mallet_out + ".outputstate.gz")
    c.default('mallet_output', mallet_out + ".outputstate")
    c.default('mallet_doctopics_output', mallet_out + ".doctopics")
    c.default('mallet_optimize_interval', 10)
    c.default('num_iterations', 500)

    # For dynamically generated metadata file, define task_attributes_file with
    # targets [$ENTITYTYPE$_metadata_file]
    c.default('metadata_filenames', {})
    metadata_entities = ('datasets','documents','word_types',
            'word_tokens','analyses','topics')
    c.default('metadata_dir', join(c['dataset_dir'], 'metadata'))
    if not os.path.exists(c['metadata_dir']):
        os.makedirs(c['metadata_dir'])
    for entity_type in metadata_entities:
        if entity_type not in c['metadata_filenames']:
            c['metadata_filenames'][entity_type] = join(c['metadata_dir'], entity_type) + '.json'

    c.default('markup_dir', join(c['dataset_dir'], c['analysis_name']) + '-markup')

    # Metrics
    # See the documentation or look in metric_scripts for a complete list of
    # available metrics
    c.default('topic_metrics', ["token_count", "type_count", "document_entropy", "word_entropy"])
    if 'topic_metric_args' in c:
        tmp_topic_metric_args = defaultdict(dict)
        tmp_topic_metric_args.update(c['topic_metric_args'])
        c['topic_metric_args'] = tmp_topic_metric_args
    else:
        c['topic_metric_args'] = defaultdict(dict)
    c.default('pairwise_topic_metrics', ["document_correlation", "word_correlation"])

    if 'pairwise_topic_metric_args' in c:
        tmp_pairwise_topic_metric_args = defaultdict(dict)
        tmp_pairwise_topic_metric_args.update(c['pairwise_topic_metric_args'])
        c['pairwise_topic_metric_args'] = tmp_pairwise_topic_metric_args
    else:
        c['pairwise_topic_metric_args'] = defaultdict(dict)

    if 'cooccurrence_counts' in c:
        c['topic_metrics'].append('coherence')
        c['topic_metric_args']['coherence'].update(
                {'counts': c['cooccurrence_counts']})
        c['pairwise_topic_metrics'].append('pairwise coherence')
        c['pairwise_topic_metric_args']['pairwise coherence'].update(
                {'counts': c['cooccurrence_counts']})
    c.default('document_metrics', ['token_count', 'type_count', 'topic_entropy'])
    c.default('pairwise_document_metrics', ['word_correlation', 'topic_correlation'])
    c.default('name_schemes', [TopNTopicNamer(c['dataset_name'], c['analysis_name'], 3)])

    # Graph-based Visualization
    c.default('java_base', os.curdir + "/java")
    c.default('java_bin', c['java_base'] + "/bin")
    c.default('graph_builder_class', "edu.byu.nlp.topicvis.TopicMapGraphBuilder")
    c.default('graphs_min_value', 1)
    c.default('graphs_pairwise_metric', "Document Correlation")

    if settings.DBTYPE=='sqlite3':
        c.default('yamba_file', os.path.join(c['base_dir'], settings.SQLITE_CONFIG['NAME']))
        if not os.path.exists(c['yamba_file']):
            print "Initializing database..."
            os.system("python topic_modeling/manage.py syncdb --noinput > /dev/null")
        c.default('db_jar', 'sqlitejdbc-v056.jar')
        c.default('jdbc_path', "jdbc:sqlite:" + c['yamba_file'])
    elif settings.DBTYPE=='mysql':
        c.default('mysql_server', settings.MYSQL_CONFIG['SERVER'])
        c.default('mysql_db', settings.MYSQL_CONFIG['NAME'])
        c.default('mysql_user', settings.MYSQL_CONFIG['USER'])
        c.default('mysql_password', settings.MYSQL_CONFIG['PASSWORD'])
        c.default('db_jar', 'mysql-connector-java-5.1.18-bin.jar')
        c.default('jdbc_path', 'jdbc:mysql://%s/%s?user=%s\&password=%s'
                % (c['mysql_server'], c['mysql_db'], c['mysql_user'], c['mysql_password']))
    else: raise Exception("Unknown database type '" + settings.DBTYPE + "'")
    return c

build_script = get_buildscript(build)
config = create_config(build_script)

# vim: et sw=4 sts=4
