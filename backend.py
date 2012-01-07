#!/usr/bin/python
## -*- coding: utf-8 -*-

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

# The doit build file for the Topical Guide.
#
# You can either invoke this file directly (./backend.py) or install doit and run
# `doit` in the same directory as this file
#
# Useful commands:
#  backend.py list #Lists the available top-level tasks (sub-tasks are not displayed)
#  backend.py #Builds everything!
#  backend.py clean -c mallet #Cleans the mallet files
#  backend.py metrics #Computes all metrics
#  backend.py topic_metrics #Computes just the topic metrics
#  backend.py topic_metrics:document_entropy #Computes just the document entropy topic metric
#  backend.py clean topic_metrics:document_entropy #Cleans just the document entropy topic metric
#
#TODO:
#  Allow specification of multiple num_topics
#

import codecs
import hashlib
import os
import sys

from collections import defaultdict
from datetime import datetime
from subprocess import Popen, PIPE

from django.db.utils import DatabaseError

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from topic_modeling import settings
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory

from import_scripts.metadata import Metadata, import_dataset_metadata,\
    import_document_metadata, import_word_metadata, import_analysis_metadata,\
    import_topic_metadata
from import_scripts.dataset_import import import_dataset
from import_scripts.analysis_import import import_analysis

from helper_scripts.name_schemes.tf_itf import TfitfTopicNamer
from helper_scripts.name_schemes.top_n import TopNTopicNamer

from topic_modeling.visualize.models import Analysis, DatasetMetric, AnalysisMetric, DatasetMetricValue,\
    AnalysisMetricValue, DatasetMetaInfoValue, DocumentMetaInfoValue,\
    WordMetaInfoValue, AnalysisMetaInfoValue, TopicMetaInfoValue
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import TopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import DocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import TopicNameScheme

#build = "twitter"
build = "state_of_the_union"
#build = "kcna/kcna"
#build = "congressional_record"


#If this file is invoked directly, pass it in to the doit system for processing.
# TODO(matt): Pretty hackish, but it's a starting place.  This should be
# cleaned up when we have time.
if __name__ == "__main__":
    if not os.path.exists(".dbs"): os.mkdir(".dbs")
    sys.path.append("tools/doit")
    from doit.doit_cmd import cmd_main
    path = os.path.abspath(sys.argv[0])

    #The database file where we'll store info about this build
    db_name = ".dbs/{0}.db".format(build.replace('/','_'))

    args = ['-f', path] + ['--db', db_name] + sys.argv[1:]
    sys.exit(cmd_main(args))

class Config(dict):
    overrides = {}
    
    def __getitem__(self, key):
        value = super(Config, self).__getitem__(key)
        try:
            value = value(self)
            self[key] = value
            return value
        except TypeError:
            return value
#    
    def default(self, key, value):
        if key not in self: self[key] = value
    
    def required(self, key):
        if key not in self: raise Exception("Configuration key '%s' is required")

c = Config()

filename = "build/{0}.py".format(build)
ast = compile(open(filename).read(), filename, 'exec')
eval(ast, globals(), locals())

if 'initialize_config' in locals(): locals()['initialize_config'](c)

c.required('dataset_name')
c.default('dataset_readable_name', c['dataset_name'])
c.default('dataset_description', '')


c.default('analysis_name', lambda c: "lda%stopics" % c['mallet_num_topics'])
c.default('analysis_readable_name', lambda c: "LDA %s Topics" % c['mallet_num_topics'])
c.default('analysis_description', lambda c: "Mallet LDA with %s topics" % c['mallet_num_topics'])
c.default('base_dir', os.curdir)
c.default('raw_data_base_dir', c['base_dir'] + "/raw-data")
c.default('raw_data_dir', c['raw_data_base_dir'] + "/" + c['dataset_name'])
c.default('datasets_dir', c['base_dir'] + "/datasets")
c.default('dataset_dir', c['datasets_dir'] + "/" + c['dataset_name'])
c.default('files_dir', c['dataset_dir'] + "/files")
if not os.path.exists(c['files_dir']): os.makedirs(c['files_dir'])
c.default('token_regex', r'[A-Za-z]+')

# Mallet
c.default('mallet', c['base_dir'] + "/tools/mallet/mallet")
c.default('mallet_num_topics', 50)
c.default('mallet_input_file_name', "mallet_input.txt")
c.default('mallet_input', c['dataset_dir'] + '/' + c['mallet_input_file_name'])
c.default('mallet_imported_data', c['dataset_dir'] + "/imported_data.mallet")
c.default('mallet_output_gz', "%s/%s.outputstate.gz" % (c['dataset_dir'], c['analysis_name']))
c.default('mallet_output', "%s/%s.outputstate" % (c['dataset_dir'], c['analysis_name']))
c.default('mallet_doctopics_output', "%s/%s.doctopics" % (c['dataset_dir'], c['analysis_name']))
c.default('mallet_optimize_interval', 10)
c.default('mallet_num_iterations', 500)

# For dynamically generated metadata file, define task_attributes_file with
# targets [$ENTITYTYPE$_metadata_file]
c.default('metadata_filenames', {})
metadata_entities = ('datasets','documents','words','analyses','topics')
c.default('metadata_dir', c['dataset_dir'] + '/metadata')
if not os.path.exists(c['metadata_dir']): os.makedirs(c['metadata_dir'])
for entity_type in metadata_entities:
    if entity_type not in c['metadata_filenames']:
        c['metadata_filenames'][entity_type] = '%s/%s.json' % (c['metadata_dir'], entity_type)

c.default('markup_dir', '%s/%s-markup' % (c['dataset_dir'], c['analysis_name']))

# Metrics
# See the documentation or look in metric_scripts for a complete list of
# available metrics
c.default('topic_metrics', ["token count", "type count", "document entropy", "word entropy"])
if 'topic_metric_args' in c:
    tmp_topic_metric_args = defaultdict(dict)
    tmp_topic_metric_args.update(c['topic_metric_args'])
    c['topic_metric_args'] = tmp_topic_metric_args
else:
    c['topic_metric_args'] = defaultdict(dict)
c.default('pairwise_topic_metrics', ["document correlation", "word correlation"])

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
c.default('document_metrics', ['token count', 'type count', 'topic entropy'])
c.default('pairwise_document_metrics', ['word correlation', 'topic correlation'])
c.default('name_schemes', [TopNTopicNamer(c['dataset_name'], c['analysis_name'], 3)])

# Graph-based Visualization
c.default('java_base', c['base_dir'] + "/java")
c.default('java_bin', c['java_base'] + "/bin")
c.default('graph_builder_class', "edu.byu.nlp.topicvis.TopicMapGraphBuilder")
c.default('graphs_min_value', 1)
c.default('graphs_pairwise_metric', "Document Correlation")

db_type = settings.database_type()
if db_type=='sqlite3':
    c.default('yamba_file', c['base_dir'] + "/yamba")
    if not os.path.exists(c['yamba_file']):
        print "Initializing database..."
        os.system("python topic_modeling/manage.py syncdb --noinput > /dev/null")
    c.default('db_jar', 'sqlitejdbc-v056.jar')
    c.default('jdbc_path', "jdbc:sqlite:" + c['yamba_file'])
elif db_type=='mysql':
    c.default('mysql_server', 'localhost')
    c.default('mysql_db', 'topicalguide')
    c.default('mysql_user', 'topicalguide')
    c.default('mysql_password', 'topicalguide')
    c.default('db_jar', 'mysql-connector-java-5.1.18-bin.jar')
    c.default('jdbc_path', 'jdbc:mysql://%s/%s?user=%s\&password=%s'
               % (c['mysql_server'], c['mysql_db'], c['mysql_user'], c['mysql_password']))
else: raise Exception("Unknown database type '" + db_type + "'")


print "----- Topical Guide Data Import System -----"
print "Dataset name: " + c['dataset_name']

if not os.path.exists(c['dataset_dir']): os.mkdir(c['dataset_dir'])

def dataset():
    return Dataset.objects.get(name=c['dataset_name'])

def analysis():
    return Analysis.objects.get(name=c['analysis_name'], dataset__name=c['dataset_name'])

#TODO(josh): get rid of the default document_metadata task---it's a total kludge
if not 'task_document_metadata' in locals() and not ('suppress_default_document_metadata_task' in c and c['suppress_default_document_metadata_task']):
    def make_document_metadata():
        attrs = open(c['metadata_filenames']['documents'], "w")
        attrs.write('{\n')
        for filename in os.listdir(c['files_dir']):
            attrs.write('\t"{0}": {}\n'.format(filename))
        attrs.write('}')

    def task_document_metadata():
        task = dict()
        task['targets'] = [c['metadata_filenames']['documents']]
        task['actions'] = [(make_document_metadata)]
        return task

if 'task_metadata_import' not in locals():
    def task_metadata_import():
        def import_datasets():
            try:
                dataset_metadata = Metadata(c['metadata_filenames']['datasets'])
                import_dataset_metadata(dataset(), dataset_metadata)
            except Dataset.DoesNotExist:
                pass
        def clean_datasets():
            try:
                dataset().datasetmetainfovalue_set.all().delete()
            except Dataset.DoesNotExist:
                pass
        def datasets_done(_task, _values):
            if not os.path.exists(c['metadata_filenames']['datasets']): return True
            try:
                return DatasetMetaInfoValue.objects.filter(dataset=dataset()).count() > 0
            except Dataset.DoesNotExist:
                return False
                
        def import_documents():
            try:
                document_metadata = Metadata(c['metadata_filenames']['documents'])
                import_document_metadata(dataset(), document_metadata)
            except Dataset.DoesNotExist:
                pass
        def clean_documents():
            try:
                dataset().document_set.documentmetainfovalue_set.all().delete()
            except Dataset.DoesNotExist:
                pass
        def documents_done(_task, _values):
            if not os.path.exists(c['metadata_filenames']['documents']): return True
            try:
                return DocumentMetaInfoValue.objects.filter(document__dataset=dataset()).count() > 0
            except Dataset.DoesNotExist:
                return False
        
        def import_words():
            try:
                word_metadata = Metadata(c['metadata_filenames']['words'])
                import_word_metadata(dataset(), word_metadata)
            except Dataset.DoesNotExist:
                pass
        def clean_words():
            try:
                dataset().word_set.wordmetainfovalue_set.all().delete()
            except Dataset.DoesNotExist:
                pass
        def words_done(_task, _values):
            if not os.path.exists(c['metadata_filenames']['words']): return True
            try:
                return WordMetaInfoValue.objects.filter(word__dataset=dataset()).count() > 0
            except Dataset.DoesNotExist:
                    return False
        
        for entity in ('datasets','documents','words'):#metadata_entities:
            task = dict()
            task['name'] = entity
            task['task_dep'] = ['dataset_import']
            task['actions'] = [(locals()['import_'+entity])]
            task['clean'] = [(locals()['clean_'+entity])]
            task['uptodate'] = [locals()[entity+'_done']]
            yield task
        
        
        def import_analyses():
            try:
                analysis_metadata = Metadata(c['metadata_filenames']['analyses'])
                import_analysis_metadata(analysis(), analysis_metadata)
            except Analysis.DoesNotExist:
                pass
        def clean_analyses():
            try:
                analysis().analysismetainfovalue_set.all().delete()
            except Analysis.DoesNotExist:
                pass
        def analyses_done(_task, _values):
            if not os.path.exists(c['metadata_filenames']['analyses']): return True
            try:
                return AnalysisMetaInfoValue.objects.filter(analysis=analysis()).count() > 0
            except Dataset.DoesNotExist,Analysis.DoesNotExist:
                return False
        
        def import_topics():
            try:
                topic_metadata = Metadata(c['metadata_filenames']['topics'])
                import_topic_metadata(analysis(), topic_metadata)
            except Analysis.DoesNotExist:
                pass
        def clean_topics():
            try:
                analysis().topic_set.topicmetainfovalue_set.all().delete()
            except Analysis.DoesNotExist:
                pass
        def topics_done(_task, _values):
            if not os.path.exists(c['metadata_filenames']['topics']): return True
            try:
                return TopicMetaInfoValue.objects.filter(topic__analysis=analysis()).count() > 0
            except Dataset.DoesNotExist,Analysis.DoesNotExist:
                    return False
        
        for entity in ('analyses','topics'):
            task = dict()
            task['name'] = entity
            task['task_dep'] = ['analysis_import']
            task['actions'] = [(locals()['import_'+entity])]
            task['clean'] = [(locals()['clean_'+entity])]
            task['uptodate'] = [locals()[entity+'_done']]
            yield task

if 'task_mallet_input' not in locals():
    def task_mallet_input():
        def make_token_file(docs_dir, output_file):
            w = codecs.open(output_file, 'w', 'utf-8')
            
            for root, dirs, files in os.walk(docs_dir):
                for f in files:
                    path = '{0}/{1}'.format(root, f)
                    # the [1:] takes off a leading /
                    partial_root = root.replace(docs_dir, '')[1:]
                    if partial_root:
                        mallet_path = '{0}/{1}'.format(partial_root, f)
                    else:
                        mallet_path = f
                    text = open(path).read().decode('utf-8').strip().replace('\n',' ').replace('\r',' ')
                    w.write(u'{0} all {1}'.format(mallet_path, text))
                    w.write(u'\n')
        
        def utd(_task, _values): return os.path.exists(c['mallet_input'])
        task = dict()
        task['targets'] = [c['mallet_input']]
        task['actions'] = [(make_token_file, [c['files_dir'], c['mallet_input']])]
        task['clean']   = ["rm -f "+c['mallet_input']]
        if 'task_extract_data' in globals():
            task['task_dep'] = ['extract_data']
        task['uptodate'] = [utd]
#        task['file_dep'] = [files_dir]
        return task

if 'task_mallet_imported_data' not in locals():
    def task_mallet_imported_data():
        task = dict()
        task['targets'] = [c['mallet_imported_data']]
        
        cmd = '%s import-dir --input %s --output %s --keep-sequence --set-source-by-name --source-name-prefix "file:%s/%s/" --remove-stopwords' \
            % (c['mallet'], c['files_dir'], c['mallet_imported_data'], os.getcwd(), c['files_dir'])
        
        if 'extra_stopwords_file' in c:
            cmd += ' --extra-stopwords ' + c['extra_stopwords_file']
        
        if 'token_regex' in c:
            cmd += " --token-regex " + c['token_regex']
        
        task['actions'] = [cmd]
        task['file_dep'] = [c['mallet_input']]
        task['clean'] = ["rm -f " + c['mallet_imported_data']]
        return task

if 'task_mallet_output_gz' not in locals():
    def task_mallet_output_gz():
        task = dict()
        task['targets'] = [c['mallet_output_gz'], c['mallet_doctopics_output']]
        task['actions'] = ['%s train-topics --input %s --optimize-interval %s --num-iterations %s --num-topics %s --output-state %s --output-doc-topics %s' \
                   % (c['mallet'], c['mallet_imported_data'], c['mallet_optimize_interval'], c['mallet_num_iterations'], c['num_topics'], c['mallet_output_gz'], c['mallet_doctopics_output'])]
        task['file_dep'] = [c['mallet_imported_data']]
        task['clean'] = ["rm -f " + c['mallet_output_gz'], "rm -f " + c['mallet_doctopics_output']]
        return task

if 'task_mallet_output' not in locals():
    def task_mallet_output():
        task = dict()
        task['targets'] = [c['mallet_output']]
        task['actions'] = ["zcat %s > %s" % (c['mallet_output_gz'], c['mallet_output'])]
        task['file_dep'] = [c['mallet_output_gz']]
        task['clean'] = ["rm -f " + c['mallet_output']]
        return task

if 'task_mallet' not in locals():
    def task_mallet():
        return {'actions':None, 'task_dep': ['mallet_input', 'mallet_imported_data', 'mallet_output_gz', 'mallet_output']}


if 'task_dataset_import' not in locals():
    def task_dataset_import():
        def utd(_task, _values):
            try:
                dataset()
                print 'dataset ' + c['dataset_name'] + ' in database'
                return True
            except (Dataset.DoesNotExist,DatabaseError):
                print 'dataset ' + c['dataset_name'] + ' NOT in database'
                return False
        
        def remove_dataset():
            print "remove_dataset(%s)" % c['dataset_name']
            try:
                dataset.delete()
            except Dataset.DoesNotExist:
                pass
        
        # TODO(matt): clean up and possibly rename dataset_import.py and
        # analysis_import.py, now that we are using this build script - we don't
        #  need standalone scripts anymore for that stuff
        task = dict()
        task['actions'] = [(import_dataset, [c['dataset_name'], c['dataset_readable_name'], c['dataset_description'], c['mallet_output'], c['metadata_filenames'], c['dataset_dir'], c['files_dir']])]
        task['file_dep'] = [c['mallet_output'], c['metadata_filenames']['documents']]
        task['clean'] = [(remove_dataset, [])]
        task['uptodate'] = [utd]
        return task

if 'task_analysis_import' not in locals():
    def task_analysis_import():
        def utd(_task, _values):
            try:
                analysis()
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist):
                return False
        
        def remove_analysis():
            try:
                print 'remove_analysis(%s)' % c['analysis_name']
                analysis().delete()
            except (Dataset.DoesNotExist, Analysis.DoesNotExist):
                pass
            
        task = dict()
        task['actions'] = [(import_analysis, [c['dataset_name'], c['analysis_name'], c['analysis_readable_name'], c['analysis_description'],
                          c['markup_dir'], c['mallet_output'], c['mallet_input'], c['metadata_filenames'], c['token_regex']])]
        task['file_dep'] = [c['mallet_output'], c['mallet_input'], c['metadata_filenames']['documents']]
        task['clean'] = [
            (remove_analysis),
            "rm -rf {0}".format(c['markup_dir'])
        ]
        task['task_dep'] = ['dataset_import']
        task['uptodate'] = [utd]
        return task

if 'task_name_schemes' not in locals():
    def task_name_schemes():
        def scheme_in_database(ns):
            try:
                TopicNameScheme.objects.get(analysis=analysis(), name=ns.scheme_name())
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicNameScheme.DoesNotExist):
                return False
        def generate_names(ns):
            ns.name_all_topics()
        def clean_names(ns):
            ns.unname_all_topics()

        print "Available topic name schemes: " + u', '.join([ns.scheme_name() for ns in c['name_schemes']])
        for ns in c['name_schemes']:
            def utd(_task, _values): return scheme_in_database(ns)
            task = dict()
            task['name'] = ns.scheme_name()
            task['actions'] = [(generate_names, [ns])]
            task['task_dep'] = ['analysis_import']
            task['clean'] = [(clean_names,[ns])]
            task['uptodate'] = [utd]
            yield task

if 'task_dataset_metrics' not in locals():
    def task_dataset_metrics():
        from metric_scripts.datasets import metrics
        def metric_in_database(dataset_metric):
            for name in dataset_metric.metric_names_generated(c['dataset_name']):
                try:
                    DatasetMetricValue.objects.get(metric__name=name, dataset__name=c['dataset_name'])
                except DatasetMetricValue.DoesNotExist:
                    return False
            return True
        
        def import_metric(dataset_metric):
            start_time = datetime.now()
            print 'Adding %s...' % dataset_metric,
            sys.stdout.flush()
            
            dataset = dataset()
            
            try:
                metrics[dataset_metric].add_metric(dataset)
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()
        
        def clean_metric(dataset_metric):
            names = metrics[dataset_metric].metric_names_generated(dataset)
            for name in names:
                DatasetMetric.objects.get(name=name).delete()
        
        print "Available dataset metrics: " + u', '.join(metrics)
        for metric_name,metric in metrics.iteritems():
            def utd(_task, _values): return metric_in_database(metric)
            task = dict()
            task['name'] = metric_name.replace(' ', '_')
            task['actions'] = [(import_metric, [metric_name])]
            task['clean'] = [(clean_metric, [metric_name])]
            task['task_dep'] = ['dataset_import']
            task['uptodate'] = [utd]
            yield task

if 'task_analysis_metrics' not in locals():
    def task_analysis_metrics():
        from metric_scripts.analyses import metrics
        def metric_in_database(analysis_metric):
            for name in analysis_metric.metric_names_generated(c['analysis_name']):
                try:
                    AnalysisMetricValue.objects.get(metric__name=name, analysis__name=c['analysis_name'])
                except AnalysisMetricValue.DoesNotExist:
                    return False
            return True
        
        def import_metric(analysis_metric):
            start_time = datetime.now()
            print 'Adding %s...' % analysis_metric,
            sys.stdout.flush()
            
            try:
                metrics[analysis_metric].add_metric(analysis())
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()
        
        def clean_metric(analysis_metric):
            names = metrics[analysis_metric].metric_names_generated(analysis())
            for name in names:
                AnalysisMetric.objects.get(name=name).delete()
        
        print "Available analysis metrics: " + u', '.join(metrics)
        for metric_name, metric in metrics.iteritems():
            def utd(_task, _values): return metric_in_database(metric)
            task = dict()
            task['name'] = metric_name.replace(' ', '_')
            task['actions'] = [(import_metric, [metric_name])]
            task['clean'] = [(clean_metric, [metric_name])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

if 'task_topic_metrics' not in locals():
    def task_topic_metrics():
        from metric_scripts.topics import metrics

        def metric_in_database(topic_metric):
            try:
                names = metrics[topic_metric].metric_names_generated(
                        c['dataset_name'], c['analysis_name'])
                for name in names:
                    TopicMetric.objects.get(analysis=analysis, name=name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist,
                    TopicMetric.DoesNotExist):
                return False

        def import_metric(topic_metric):
            start_time = datetime.now()
            print 'Adding %s...' % topic_metric,
            sys.stdout.flush()
            try:
                metrics[topic_metric].add_metric(c['dataset_name'], c['analysis_name'],
                        **c['topic_metric_args'][topic_metric])
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()

        def clean_metric(topic_metric):
            print "Removing topic metric: " + topic_metric
            names = metrics[topic_metric].metric_names_generated(c['dataset_name'],
                    c['analysis_name'])
            for topic_metric_name in names:
                TopicMetric.objects.get(analysis=analysis,
                        name=topic_metric_name).delete()

        print "Available topic metrics: " + u', '.join(c['topic_metrics'])
        for topic_metric in c['topic_metrics']:
            def utd(_task, _values): return metric_in_database(topic_metric)
            task = dict()
            task['name'] = topic_metric.replace(' ', '_')
            task['actions'] = [(import_metric, [topic_metric])]
            task['clean'] = [(clean_metric, [topic_metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

if 'task_pairwise_topic_metrics' not in locals():
    def task_pairwise_topic_metrics():
        from metric_scripts.topics import pairwise_metrics

        def metric_in_database(metric):
            try:
                names = pairwise_metrics[metric].metric_names_generated(
                        c['dataset_name'], c['analysis_name'])
                for name in names:
                    PairwiseTopicMetric.objects.get(analysis=analysis,
                            name=name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist,
                    PairwiseTopicMetric.DoesNotExist):
                return False

        def import_metric(metric):
            start_time = datetime.now()
            print 'Adding %s...' % metric,
            sys.stdout.flush()
            try:
                pairwise_metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()

        def clean_metric(metric):
            print "Removing pairwise topic metric: " + metric
            names = pairwise_metrics[metric].metric_names_generated(
                    c['dataset_name'], c['analysis_name'])
            for metric_name in names:
                PairwiseTopicMetric.objects.get(analysis=analysis,
                        name=metric_name).delete()

        print "Available pairwise topic metrics: " + u', '.join(
                c['pairwise_topic_metrics'])
        for pairwise_topic_metric in c['pairwise_topic_metrics']:
            def utd(_task, _values): return metric_in_database(pairwise_topic_metric)
            task = dict()
            task['name'] = pairwise_topic_metric.replace(' ', '_')
            task['actions'] = [(import_metric, [pairwise_topic_metric])]
            task['clean'] = [(clean_metric, [pairwise_topic_metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

if 'task_document_metrics' not in locals():
    def task_document_metrics():
        from metric_scripts.documents import metrics

        def metric_in_database(metric):
            try:
                names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
                for name in names:
                    DocumentMetric.objects.get(analysis=analysis, name=name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist, DocumentMetric.DoesNotExist):
                return False

        def import_metric(metric):
            start_time = datetime.now()
            print 'Adding %s...' % metric,
            sys.stdout.flush()
            try:
                metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()

        def clean_metric(metric):
            print "Removing document metric: " + metric
            names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
            for metric_name in names:
                metric = DocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()

        print "Available document metrics: " + u', '.join(metrics)
        for metric in metrics:
            def utd(_task, _values): return metric_in_database(metric)
            task = dict()
            task['name'] = metric.replace(' ', '_')
            task['actions'] = [(import_metric, [metric])]
            task['clean'] = [(clean_metric, [metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

if 'task_pairwise_document_metrics' not in locals():
    def task_pairwise_document_metrics():
        from metric_scripts.documents import pairwise_metrics

        def metric_in_database(metric):
            try:
                names = pairwise_metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
                for name in names:
                    PairwiseDocumentMetric.objects.get(analysis=analysis, name=name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist, PairwiseDocumentMetric.DoesNotExist):
                return False

        def import_metric(metric):
            start_time = datetime.now()
            print 'Adding %s...' % metric,
            sys.stdout.flush()
            try:
                pairwise_metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                end_time = datetime.now()
                print '  Done', end_time - start_time
                sys.stdout.flush()
            except KeyError as e:
                print "\nI couldn't find the metric you specified:", e
                sys.stdout.flush()
            except RuntimeError as e:
                print "\nThere was an error importing the specified metric:", e
                sys.stdout.flush()

        def clean_metric(metric):
            print "Removing pairwise document metric: " + metric
            names = pairwise_metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
            if isinstance(names, basestring): names = [names]
            for metric_name in names:
                PairwiseDocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()

        print "Available pairwise document metrics: " + u', '.join(pairwise_metrics)
        for metric in c['pairwise_document_metrics']:
            def utd(_task, _values): return metric_in_database(metric)
            task = dict()
            task['name'] = metric.replace(' ', '_')
            task['actions'] = [(import_metric, [metric])]
            task['clean'] = [(clean_metric, [metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

if 'task_metrics' not in locals():
    def task_metrics():
        return {'actions':None, 'task_dep': ['analysis_import', 'topic_metrics', 'pairwise_topic_metrics', 'document_metrics', 'pairwise_document_metrics']}

def task_hash_java():
    def _cmd_output(cmd):
        return Popen(cmd, shell=True, bufsize=512, stdout=PIPE).stdout.read()
    
    def _directory_timestamp(dir_):
        return str(os.path.getmtime(dir_))
    
    def _hash(txt):
        hasher = hashlib.md5()
        hasher.update(txt)
        return hasher.hexdigest()
    
    def _directory_recursive_hash(dir_):
        if not os.path.exists(dir): return "0"
        return hash(_cmd_output("find {dir} -type f -print0 | xargs -0 md5sum".format(dir=dir_)))
    
    return {'actions': [(_directory_recursive_hash, [c['java_base']])]}

if 'task_compile_java' not in locals():
    def task_compile_java():
        actions = ["cd {0} && ant -lib lib".format(c['java_base'])]
        result_deps = ['hash_java']
        clean = ['rm -rf ' + c['java_bin']]
        return {'actions':actions, 'result_dep':result_deps, 'clean':clean}

if 'task_graphs' not in locals():
    def task_graphs():
        classpath = '{0}:{1}/lib/gephi-toolkit.jar:{1}/lib/statnlp-rev562.jar:{1}/lib/{2}'.format(c['java_bin'], c['java_base'], c['db_jar'])
        
        
        for ns in c['name_schemes']:
            def utd(_task, _values): return os.path.exists(graphs_img_dir)
                
            task = dict()
            graphs_img_dir = "{0}/topic_maps/{1}/{2}".format(c['dataset_dir'], c['analysis_name'], ns.scheme_name())
            graphs_unlinked_img_dir = graphs_img_dir + "-unlinked"
            gexf_file_name = "{0}/full_graph.gexf".format(graphs_img_dir)
            
            task['actions'] = [
                'java -cp {0} {1} {2} {3} {4} {5} "{6}" {7} {8} {9} {10}'
                .format(classpath,c['graph_builder_class'],c['graphs_min_value'],c['dataset_name'],c['analysis_name'],ns.scheme_name(),c['graphs_pairwise_metric'], c['jdbc_path'], graphs_unlinked_img_dir, graphs_img_dir, gexf_file_name)
            ]
            task['task_dep'] = ['pairwise_topic_metrics', 'name_schemes', 'compile_java']
            task['clean'] =  [
                'rm -rf '+graphs_unlinked_img_dir,
                'rm -rf '+graphs_img_dir
            ]
            task['name'] = ns.scheme_name()
            task['uptodate'] = [utd]
            yield task
        
#
#def task_reset_db():
#    actions = ['yes "yes" | python topic_modeling/manage.py reset visualize']
#    return {'actions':actions}
