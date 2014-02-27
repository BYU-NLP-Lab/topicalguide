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
import datetime
import hashlib
import os
from os.path import join, dirname
import sys
import imp

from topic_modeling.tools import setup_logging, logging
setup_logging()
logger = logging.getLogger('root')

if __name__ == "__main__":
    logger.warn("This file is only meant to be run by doit. "
                 "use ./run_import.py to run the backend import")

from collections import defaultdict
from subprocess import Popen, PIPE

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from topic_modeling import settings
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory

from django.db.utils import DatabaseError

from import_scripts.metadata import Metadata, import_dataset_metadata,\
    import_document_metadata, import_word_type_metadata, import_word_token_metadata, \
    import_analysis_metadata, import_topic_metadata
from import_scripts import dataset_import
from import_scripts import analysis_import

from helper_scripts.name_schemes.tf_itf import TfitfTopicNamer
from helper_scripts.name_schemes.top_n import TopNTopicNamer

from topic_modeling.visualize.models import (Analysis, DatasetMetric,
        AnalysisMetric, DatasetMetricValue, AnalysisMetricValue,
        DatasetMetaInfoValue, DocumentMetaInfoValue, WordTypeMetaInfoValue,
        WordTokenMetaInfoValue, AnalysisMetaInfoValue, TopicMetaInfoValue,
        WordType, WordToken, Document, Topic, PairwiseTopicMetricValue,
        DocumentMetricValue)
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import TopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import DocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import TopicNameScheme

try:
    from import_tool.local_settings import LOCAL_DIR
except ImportError:
    print >> sys.stderr, "Import error looking for local_settings.py."\
            "Look at topic_modeling/local_settings.py.sample for help"
    raise

class DoitTask:
    '''A class to organize our tasks more sanely'''
    name = None
    basename = None
    task_dep = []
    targets = []

    def __init__(self, *args):
        self.args = args

    def __call__(self):
        def meta():
            return self.to_dict()
        return meta

    def action(self, *args, **kwds):
        '''Perform the data'''
        raise NotImplemented

    def clean(self):
        '''Clean up data'''
        raise NotImplemented

    def uptodate(self):
        '''Return a boolean, indicating whether this task has been done already
        '''
        return False

    def actions(self):
        '''Returns all of the action items'''
        if self.args:
            return [(self.action, self.args)]
        return [self.action]

    def to_dict(self):
        '''Serve up a nice dictionary that doit wants'''
        task = {'targets': self.targets,
                'task_dep': self.task_dep,
                'actions': self.actions(),
                'clean': [self.clean],
                'uptodate': [self.uptodate]}
        if self.name:
            task['name'] = self.name
        # if self.basename:
            # task['basename'] = self.basename
        return task

'''Ok, so to start out we import a config script (that lives in build/) and
let it pollute our namespace. Then we go through and set up an aggregious
number of config options, making sure not to override any options that may
have been set by our config script.
'''
BASE_DIR = os.path.abspath(dirname(dirname(__file__)))

from config import config
c = config


# gets info from the database, this will represent all of the documents
def dataset():
    return Dataset.objects.get(name=c['dataset_name'])

def analysis():
    return Analysis.objects.get(name=c['analysis_name'], dataset__name=c['dataset_name'])






#-----------------------------------IMPORT THINGS----------------------------#

# After we import things we run the task 'analysis_import'
#~ if 'task_metadata_import' not in locals():
    #~ def task_metadata_import():
#~ 
        #~ class ImportTask(DoitTask):
            #~ #task_dep = ['analysis_import']
            #~ 
            #~ def action(self):
                #~ try:
                    #~ 
                    #~ metadata = Metadata(c['metadata_filenames'][self.name])
                    #~ 
                    #~ self.fn[0](dataset(), metadata)
                #~ except Dataset.DoesNotExist:
                    #~ raise Exception('Trying to run a metadata import for '
                            #~ '%s, and the dataset doesn\'t exist!' % self.name)
#~ 
        #~ class ImportDatasets(ImportTask):
            #~ '''A task to import all the meta info for the dataset'''
#~ 
            #~ name = 'datasets'
            #~ fn = [import_dataset_metadata]
#~ 
            #~ def clean(self):
                #~ try:
                    #~ dataset().metainfovalues.all().delete()
                #~ except Dataset.DoesNotExist:
                    #~ pass
#~ 
            #~ #c['metadata_filenames']['datasets'] = /local/cj264/topicalguide/working/datasets/Conference_Talks_on_Agency/metadata/datasets.json
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['datasets']):
                    #~ return True
                #~ try:
                    #~ return DatasetMetaInfoValue.objects.filter(dataset=dataset()).count() > 0
                #~ except Dataset.DoesNotExist:
                    #~ return False
#~ 
        #~ class ImportDocuments(ImportTask):
            #~ '''A task to import all the metainfo for all documents in the dataset'''
#~ 
            #~ name = 'documents'
            #~ fn = [import_document_metadata]
#~ 
            #~ def clean(self):
                #~ try:
                    #~ for doc in dataset().documents.all():
                        #~ doc.metainfovalues.all().delete()
                #~ except Dataset.DoesNotExist:
                    #~ pass
#~ 
            #~ #e.g.: c['metadata_filenames']['documents'] = /local/cj264/topicalguide/working/datasets/Conference_Talks_on_Agency/metadata/documents.json
            #~ #print c['metadata_filenames']['documents']
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['documents']): return True
                #~ try:
                    #~ return DocumentMetaInfoValue.objects.filter(
                            #~ document__dataset=dataset()
                        #~ ).count() > 0
                #~ except Dataset.DoesNotExist:
                    #~ return False
#~ 
        #~ class ImportWordTypes(ImportTask):
            #~ '''A task to import all the metainfo for all the word types'''
#~ 
            #~ name = 'word_types'
            #~ fn = [import_word_type_metadata]
#~ 
            #~ def clean(self):
                #~ try:
                    #~ for word_type in WordType.objects.filter(tokens__doc__dataset=dataset()):
                        #~ word_type.metainfovalues.all().delete()
                #~ except Dataset.DoesNotExist:
                    #~ pass
#~ 
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['word_types']):
                    #~ return True
                #~ try:
                    #~ return WordTypeMetaInfoValue.objects.filter(word_type__tokens__doc__dataset=dataset()).count() > 0
                #~ except Dataset.DoesNotExist:
                        #~ return False
#~ 
        #~ class ImportWordTokens(ImportTask):
            #~ '''A task to import all the metainfo for all the word tokens'''
#~ 
            #~ name = 'word_tokens'
            #~ fn = [import_word_token_metadata]
#~ 
            #~ def clean(self):
                #~ try:
                    #~ for word_token in WordToken.objects.filter(doc__dataset=dataset()):
                        #~ word_token.metainfovalues.all().delete()
                #~ except Dataset.DoesNotExist:
                    #~ pass
#~ 
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['word_tokens']):
                    #~ return True
                #~ try:
                    #~ return WordTokenMetaInfoValue.objects.filter(word_token__doc__dataset=dataset()).count() > 0
                #~ except Dataset.DoesNotExist:
                        #~ return False
#~ 
        #~ yield ImportDatasets().to_dict()
        #~ yield ImportDocuments().to_dict()
        #~ yield ImportWordTypes().to_dict()
        #~ yield ImportWordTokens().to_dict()
#~ 
        #~ class ImportATask(DoitTask):
            #~ #task_dep = ['analysis_import']
#~ 
            #~ def action(self):
                #~ try:
                    #~ metadata = Metadata(c['metadata_filenames'][self.name])
                    #~ self.fn(analysis(), metadata)
                #~ except Analysis.DoesNotExist:
                    #~ raise Exception('Trying to run a metadata import for '
                            #~ '%s, and the analysis doesn\'t exist!' % self.name)
#~ 
        #~ class ImportAnalysis(ImportATask):
#~ 
            #~ name = 'analysis'
            #~ fn = [import_analysis_metadata]
#~ 
            #~ def clean(self):
                #~ try:
                    #~ analysis().metainfovalues.all().delete()
                #~ except Analysis.DoesNotExist:
                    #~ pass
#~ 
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['analyses']): return True
                #~ try:
                    #~ return AnalysisMetaInfoValue.objects.filter(analysis=analysis()).count() > 0
                #~ except Dataset.DoesNotExist,Analysis.DoesNotExist:
                    #~ return False
#~ 
        #~ class ImportTopics(ImportATask):
#~ 
            #~ name = 'topics'
            #~ fn = [import_topic_metadata]
#~ 
            #~ def clean_topics(self):
                #~ try:
                    #~ for topic in analysis().topics.all():
                        #~ topic.metainfovalues.all().delete()
                #~ except Analysis.DoesNotExist:
                    #~ pass
#~ 
            #~ def uptodate(self, _task, _values):
                #~ if not os.path.exists(c['metadata_filenames']['topics']): return True
                #~ try:
                    #~ return TopicMetaInfoValue.objects.filter(topic__analysis=analysis()).count() > 0
                #~ except Dataset.DoesNotExist,Analysis.DoesNotExist:
                        #~ return False
#~ 
        #~ yield ImportAnalysis().to_dict()
        #~ yield ImportTopics().to_dict()

#--------------------------------MALLET TASKS--------------------------------#
'''Next we have several tasks that deal with mallet
- preparing + importing the data
- running mallet train-topics
- extracting the output
'''

#~ if 'task_mallet_input' not in locals():
    #~ class MalletInput(DoitTask):
#~ 
        #~ basename = 'mallet_input'
        #~ clean = 'rm -f '+c['mallet_input']
        #~ targets = [c['mallet_input']]
        #~ if 'task_extract_data' in globals():
            #~ task_dep = ['extract_data']
#~ 
        #~ def action(self, docs_dir, output_file):
            #~ count = 0
            #~ for root, dirs, files in os.walk(docs_dir):
                #~ for f in files:
                    #~ count += 1
                    #~ path = '{0}/{1}'.format(root, f)
                    #~ # the [1:] takes off a leading /
                    #~ partial_root = root.replace(docs_dir, '')[1:]
                    #~ if partial_root:
                        #~ mallet_path = '{0}/{1}'.format(partial_root, f)
                    #~ else:
                        #~ mallet_path = f
                    #~ text = open(path).read().decode('utf-8').strip().replace('\n',' ').replace('\r',' ')
                    #~ w.write(u'{0} all {1}'.format(mallet_path, text))
                    #~ w.write(u'\n')
#~ 
            #~ if not count:
                #~ raise Exception('No files processed')
#~ 
        #~ def uptodate(self, _task, _values):
            #~ return os.path.exists(c['mallet_input'])
#~ 
    #~ task_mallet_input = MalletInput(c['files_dir'], c['mallet_input'])()

#~ if 'task_mallet_imported_data' not in locals():
    #~ def task_mallet_imported_data():
        #~ task = dict()
        #~ task['targets'] = [c['mallet_imported_data']]
        #~ print "config items:"
        #~ print c['mallet']
        #~ print c['files_dir']
        #~ print c['mallet_imported_data']
        #~ print c['files_dir']
        #~ #raise Exception("mallet_imported_data")
        #~ #TODO why is import-dir being used?
        #~ #this means compiling data to single file is unnecessary
        #~ cmd = '%s import-dir --input %s --output %s --keep-sequence --set-source-by-name --source-name-prefix "file:%s/%s/" --remove-stopwords' \
            #~ % (c['mallet'], c['files_dir'], c['mallet_imported_data'], os.getcwd(), c['files_dir'])
#~ 
        #~ if 'extra_stopwords_file' in c:
            #~ cmd += ' --extra-stopwords ' + c['extra_stopwords_file']
#~ 
        #~ if 'token_regex' in c and c['token_regex']:
            #~ cmd += " --token-regex " + c['token_regex']
#~ 
        #~ task['actions'] = [cmd]
        #~ task['file_dep'] = [c['mallet_input']]
        #~ task['clean'] = ["rm -f " + c['mallet_imported_data']]
        #~ return task

#~ if 'task_mallet_output_gz' not in locals():
    #~ def task_mallet_output_gz():
        #~ task = dict()
        #~ 
        #~ task['targets'] = [c['mallet_output_gz'], c['mallet_doctopics_output']]
        #~ task['actions'] = ['%s train-topics --input %s --optimize-interval %s --num-iterations %s --num-topics %s --output-state %s --output-doc-topics %s' \
                   #~ % (c['mallet'], c['mallet_imported_data'], c['mallet_optimize_interval'], c['num_iterations'], c['num_topics'], c['mallet_output_gz'], c['mallet_doctopics_output'])]
        #~ task['file_dep'] = [c['mallet_imported_data']]
        #~ task['clean'] = ["rm -f " + c['mallet_output_gz'], "rm -f " + c['mallet_doctopics_output']]
        #~ return task
#~ 
#~ if 'task_mallet_output' not in locals():
    #~ def task_mallet_output():
        #~ task = dict()
        #~ task['targets'] = [c['mallet_output']]
        #~ task['actions'] = ["gunzip -c %s > %s" % (c['mallet_output_gz'], c['mallet_output'])]
        #~ task['file_dep'] = [c['mallet_output_gz']]
        #~ task['clean'] = ["rm -f " + c['mallet_output']]
        #~ return task
#~ 
#~ if 'task_mallet' not in locals():
    #~ def task_mallet():
        #~ return {'actions':None, 'task_dep': ['mallet_output_gz', 'mallet_output']}

#------------------------------Import things---------------------------------#
'''Here we import stuff into the database!  '''

#~ sys.stdout = sys.stderr
#~ ## it looks like this is working
#~ if 'task_dataset_import' not in locals():
    #~ def task_dataset_import():
        #~ '''Import the dataset into the Database
#~ 
        #~ 1) create a Dataset object
        #~ 2) create WordType objects for each unique word in the entire directory
        #~ @todo: we iterate through all the words *twice*, once to make wordtypes,
               #~ and again to make the wordtokens!
        #~ 3) create Document objects for each file in the dataset directory
        #~ 4) create WordToken objects for each "word" (found by c['token_regex'])
#~ 
        #~ '''
#~ 
        #~ def utd(_task, _values):
            #~ return dataset_import.check_dataset(c['dataset_name'])
        #~ '''
            #~ try:
                #~ _dataset = dataset()
                #~ print 'dataset ' + c['dataset_name'] + ' in database'
                #~ return Document.objects.filter(dataset=_dataset).count() > 0
            #~ except (Dataset.DoesNotExist,DatabaseError):
                #~ print 'dataset ' + c['dataset_name'] + ' NOT in database'
                #~ return False
        #~ '''
#~ 
        #~ def remove_dataset():
            #~ ## !!! This still doesn't work properly...
            #~ raise NotImplementedError('This needs to be fixed')
            #~ print>>sys.stderr, "remove_dataset(%s)" % c['dataset_name']
            #~ try:
                #~ dataset_ = dataset()
                #~ for document in Document.objects.filter(dataset=dataset_):
                    #~ WordToken.objects.raw('DELETE from visualize_wordtoken WHERE document_id=%d'
                            #~ % document.id)
                    #~ document.delete()
                #~ # WordType.objects.filter(document__dataset=dataset_).delete()
                #~ # Document.objects.filter(dataset=dataset_).delete()
                #~ print>>sys.stderr, "dataset", [dataset_]
                #~ dataset_.delete()
            #~ except Dataset.DoesNotExist:
                #~ print>>sys.stderr, "Dataset not found"
                #~ pass
#~ 
        #~ # TODO(matt): clean up and possibly rename dataset_import.py and
        #~ # analysis_import.py, now that we are using this build script - we don't
        #~ #  need standalone scripts anymore for that stuff
        #~ task = dict()
        #~ task['actions'] = [(dataset_import.import_dataset, [c['dataset_name'], c['dataset_readable_name'],
            #~ c['dataset_description'], c['metadata_filenames'], c['dataset_dir'], c['files_dir'], c['token_regex']])]
        #~ task['file_dep'] = [c['metadata_filenames']['documents']]
        #~ task['clean'] = [remove_dataset]
        #~ task['uptodate'] = [utd]
        #~ # remove_dataset()
        #~ return task

## and now this is working too!
#~ if 'task_analysis_import' not in locals():
    #~ def task_analysis_import():
        #~ '''Here we wrap import_analysis. And we import the analysis
        #~ 
        #~ 1) get (or create) a dataset object
        #~ 2) create an Analysis DB object
        #~ 3) create a Metadata dictionary
        #~ 4) parse the mallet_output file, '''
        #~ def utd(_task, _values):
            #~ return analysis_import.check_analysis(c['analysis_name'], c['dataset_name'])
        #~ '''
            #~ try:
                #~ _analysis = analysis()
                #~ return Topic.objects.filter(analysis = _analysis).count()
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist):
                #~ return False
        #~ '''
#~ 
        #~ def remove_analysis():
            #~ return analysis_import.delete_analysis(c['analysis_name'], c['dataset_name'])
        #~ '''
            #~ try:
                #~ print 'remove_analysis(%s)' % c['analysis_name']
                #~ analysis().delete()
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist):
                #~ pass
                #~ '''
#~ 
        #~ task = dict()
        #~ task['actions'] = [(analysis_import.import_analysis, [c['dataset_name'], c['analysis_name'], c['analysis_readable_name'], c['analysis_description'],
                          #~ c['markup_dir'], c['mallet_output'], c['mallet_input'], c['metadata_filenames'], c['token_regex']])]
        #~ task['file_dep'] = [c['mallet_output'], c['mallet_input'], c['metadata_filenames']['documents']]
        #~ task['clean'] = [
            #~ (remove_analysis),
            #~ "rm -rf {0}".format(c['markup_dir'])
        #~ ]
        #~ task['task_dep'] = ['dataset_import']
        #~ task['uptodate'] = [utd]
        #~ return task

## works!
#~ if 'task_name_schemes' not in locals():
    #~ def task_name_schemes():
        #~ '''This names all of our topics based on a particular scheme'''
        #~ def scheme_in_database(name_scheme_name):
            #~ try:
                #~ TopicNameScheme.objects.get(analysis=analysis(), name=name_scheme_name)
                #~ return True
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicNameScheme.DoesNotExist):
                #~ return False
        #~ def generate_names(ns):
            #~ ns.name_all_topics()
        #~ def clean_names(ns):
            #~ ns.unname_all_topics()
#~ 
        #~ print "Available topic name schemes: " + u', '.join([ns.scheme_name() for ns in c['name_schemes']])
        #~ for ns in c['name_schemes']:
            #~ utd = lambda task,vals: scheme_in_database(task.name.split(':')[-1])
            #~ task = dict()
            #~ task['name'] = ns.scheme_name()
            #~ task['actions'] = [(generate_names, [ns])]
            #~ #task['task_dep'] = ['analysis_import']
            #~ task['clean'] = [(clean_names,[ns])]
            #~ task['uptodate'] = [utd]
            #~ yield task

# this looks fine
#~ if 'task_dataset_metrics' not in locals():
    #~ def task_dataset_metrics():
        #~ '''Runs metrics on the dataset. This wraps metrics from the helper_scripts'''
        #~ from metric_scripts.datasets import metrics
        #~ def metric_in_database(metric_name):
            #~ for name in metrics[metric_name].metric_names_generated(c['dataset_name']):
                #~ try:
                    #~ DatasetMetricValue.objects.get(metric__name=name, dataset__name=c['dataset_name'])
                #~ except DatasetMetricValue.DoesNotExist:
                    #~ return False
            #~ return True
#~ 
        #~ def import_metric(dataset_metric):
            #~ start_time = datetime.datetime.now()
            #~ print 'Adding %s...' % dataset_metric,
            #~ sys.stdout.flush()
#~ 
            #~ dataset_ = dataset()
#~ 
            #~ try:
                #~ metrics[dataset_metric].add_metric(dataset_)
                #~ end_time = datetime.datetime.now()
                #~ print '  Done', end_time - start_time
                #~ sys.stdout.flush()
            #~ except KeyError as e:
                #~ print "\nI couldn't find the metric you specified:", e
                #~ sys.stdout.flush()
            #~ except RuntimeError as e:
                #~ print "\nThere was an error importing the specified metric:", e
                #~ sys.stdout.flush()
#~ 
        #~ def clean_metric(dataset_metric):
            #~ names = metrics[dataset_metric].metric_names_generated(dataset)
            #~ for name in names:
                #~ DatasetMetric.objects.get(name=name).delete()
#~ 
        #~ print "Available dataset metrics: " + u', '.join(metrics)
        #~ for metric_name in metrics:
            #~ utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            #~ task = dict()
            #~ task['name'] = metric_name.replace(' ', '_')
            #~ task['actions'] = [(import_metric, [metric_name])]
            #~ task['clean'] = [(clean_metric, [metric_name])]
            #~ #task['task_dep'] = ['dataset_import']
            #~ task['uptodate'] = [utd]
            #~ yield task

# doing well
if 'task_analysis_metrics' not in locals():
    def task_analysis_metrics():
        from metric_scripts.analyses import metrics
        def metric_in_database(metric_name):
            for name in metrics[metric_name].metric_names_generated(c['analysis_name']):
                try:
                    AnalysisMetricValue.objects.get(metric__name=name, analysis__name=c['analysis_name'])
                except AnalysisMetricValue.DoesNotExist:
                    return False
            return True

        def import_metric(analysis_metric):
            start_time = datetime.datetime.now()
            print 'Adding %s...' % analysis_metric,
            sys.stdout.flush()

            try:
                metrics[analysis_metric].add_metric(analysis())
                end_time = datetime.datetime.now()
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
        for metric_name in metrics:
            utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            task = dict()
            task['name'] = metric_name.replace(' ', '_')
            task['actions'] = [(import_metric, [metric_name])]
            task['clean'] = [(clean_metric, [metric_name])]
            #task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            yield task

# these are looking fine
if 'task_topic_metrics' not in locals():
    def task_topic_metrics():
        '''Do metrics on functions!'''
        from metric_scripts.topics import metrics

        def metric_in_database(topic_metric):
            print 'Topic metric2: ', topic_metric
            try:
                names = metrics[topic_metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
                for name in names:
                    TopicMetric.objects.get(analysis=analysis, name=name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicMetric.DoesNotExist):
                return False

        def import_metric(topic_metric):
            start_time = datetime.datetime.now()
            print 'Adding %s...' % topic_metric,
            sys.stdout.flush()
            try:
                metrics[topic_metric].add_metric(c['dataset_name'], c['analysis_name'],
                        **c['topic_metric_args'][topic_metric])
                end_time = datetime.datetime.now()
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
            utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            task = dict()
            task['name'] = topic_metric.replace(' ', '_')
            task['actions'] = [(import_metric, [topic_metric])]
            task['clean'] = [(clean_metric, [topic_metric])]
            #task['task_dep'] = ['analysis_import']
            task['uptodate'] = [utd]
            print utd(task, None)
            print 'Topic metric1: ', topic_metric
            print('Topic metrics: ', c['topic_metrics'])
            yield task
#~ 
#~ if 'task_pairwise_topic_metrics' not in locals():
    #~ def task_pairwise_topic_metrics():
        #~ from metric_scripts.topics.pairwise import metrics
#~ 
        #~ def metric_in_database(metric):
            #~ try:
                #~ names = metrics[metric].metric_names_generated(
                        #~ c['dataset_name'], c['analysis_name'])
                #~ for name in names:
                    #~ metric = PairwiseTopicMetric.objects.get(analysis=analysis,
                                #~ name=name)
                    #~ values = PairwiseTopicMetricValue.objects.filter(metric=metric)
                    #~ if not values.count():
                        #~ return False
                #~ return True
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist,
                    #~ PairwiseTopicMetric.DoesNotExist):
                #~ return False
#~ 
        #~ def import_metric(metric):
            #~ start_time = datetime.datetime.now()
            #~ print 'Adding %s...' % metric,
            #~ sys.stdout.flush()
            #~ try:
                #~ print 'yeah...'
                #~ metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                #~ end_time = datetime.datetime.now()
                #~ print '  Done', end_time - start_time
                #~ sys.stdout.flush()
            #~ except KeyError as e:
                #~ print "\nI couldn't find the metric you specified:", e
                #~ sys.stdout.flush()
            #~ except RuntimeError as e:
                #~ print "\nThere was an error importing the specified metric:", e
                #~ sys.stdout.flush()
#~ 
        #~ def clean_metric(metric):
            #~ print "Removing pairwise topic metric: " + metric
            #~ names = metrics[metric].metric_names_generated(
                    #~ c['dataset_name'], c['analysis_name'])
            #~ for metric_name in names:
                #~ PairwiseTopicMetric.objects.get(analysis=analysis,
                        #~ name=metric_name).delete()
#~ 
        #~ print "Available pairwise topic metrics: " + u', '.join(
                #~ c['pairwise_topic_metrics'])
        #~ for pairwise_topic_metric in c['pairwise_topic_metrics']:
            #~ utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            #~ task = dict()
            #~ task['name'] = pairwise_topic_metric.replace(' ', '_')
            #~ task['actions'] = [(import_metric, [pairwise_topic_metric])]
            #~ task['clean'] = [(clean_metric, [pairwise_topic_metric])]
            #~ #task['task_dep'] = ['analysis_import']
            #~ task['uptodate'] = [utd]
            #~ yield task
#~ 
#~ if 'task_document_metrics' not in locals():
    #~ def task_document_metrics():
        #~ from metric_scripts.documents import metrics
#~ 
        #~ def metric_in_database(metric):
            #~ try:
                #~ names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
                #~ for name in names:
                    #~ metric = DocumentMetric.objects.get(analysis=analysis, name=name)
                    #~ if not DocumentMetricValue.objects.filter(metric=metric).count():
                        #~ return False
                #~ return True
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist, DocumentMetric.DoesNotExist):
                #~ return False
#~ 
        #~ def import_metric(metric):
            #~ start_time = datetime.datetime.now()
            #~ print 'Adding %s...' % metric,
            #~ sys.stdout.flush()
            #~ try:
                #~ metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                #~ end_time = datetime.datetime.now()
                #~ print '  Done', end_time - start_time
                #~ sys.stdout.flush()
            #~ except KeyError as e:
                #~ print "\nI couldn't find the metric you specified:", e
                #~ sys.stdout.flush()
            #~ except RuntimeError as e:
                #~ print "\nThere was an error importing the specified metric:", e
                #~ sys.stdout.flush()
#~ 
        #~ def clean_metric(metric):
            #~ print "Removing document metric: " + metric
            #~ names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
            #~ for metric_name in names:
                #~ metric = DocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()
#~ 
        #~ print "Available document metrics: " + u', '.join(metrics)
        #~ for metric in metrics:
            #~ utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            #~ task = dict()
            #~ task['name'] = metric.replace(' ', '_')
            #~ task['actions'] = [(import_metric, [metric])]
            #~ task['clean'] = [(clean_metric, [metric])]
            #~ #task['task_dep'] = ['analysis_import']
            #~ task['uptodate'] = [utd]
            #~ yield task
#~ 
#~ if 'task_pairwise_document_metrics' not in locals():
    #~ def task_pairwise_document_metrics():
        #~ from metric_scripts.documents.pairwise import metrics
#~ 
        #~ def metric_in_database(metric):
            #~ try:
                #~ names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
                #~ for name in names:
                    #~ metric = PairwiseDocumentMetric.objects.get(analysis=analysis, name=name)
                    #~ if not PairwiseTopicMetricValue.objects.filter(metric=metric).count():
                        #~ return False
                #~ return True
            #~ except (Dataset.DoesNotExist, Analysis.DoesNotExist, PairwiseDocumentMetric.DoesNotExist):
                #~ return False
#~ 
        #~ def import_metric(metric):
            #~ start_time = datetime.datetime.now()
            #~ print 'Adding %s...' % metric,
            #~ sys.stdout.flush()
            #~ try:
                #~ metrics[metric].add_metric(c['dataset_name'], c['analysis_name'])
                #~ end_time = datetime.datetime.now()
                #~ print '  Done', end_time - start_time
                #~ sys.stdout.flush()
            #~ except KeyError as e:
                #~ print "\nI couldn't find the metric you specified:", e
                #~ sys.stdout.flush()
            #~ except RuntimeError as e:
                #~ print "\nThere was an error importing the specified metric:", e
                #~ sys.stdout.flush()
#~ 
        #~ def clean_metric(metric):
            #~ print "Removing pairwise document metric: " + metric
            #~ names = metrics[metric].metric_names_generated(c['dataset_name'], c['analysis_name'])
            #~ if isinstance(names, basestring): names = [names]
            #~ for metric_name in names:
                #~ PairwiseDocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()
#~ 
        #~ print "Available pairwise document metrics: " + u', '.join(metrics)
        #~ for metric in c['pairwise_document_metrics']:
            #~ utd = lambda task,vals: metric_in_database(task.name.split(':')[-1])
            #~ task = dict()
            #~ task['name'] = metric.replace(' ', '_')
            #~ task['actions'] = [(import_metric, [metric])]
            #~ task['clean'] = [(clean_metric, [metric])]
            #~ #task['task_dep'] = ['analysis_import']
            #~ task['uptodate'] = [utd]
            #~ yield task
#~ 
#~ if 'task_metrics' not in locals():
    #~ def task_metrics():
        #~ return {'actions':None, 'task_dep': ['topic_metrics', 'pairwise_topic_metrics', 'document_metrics', 'pairwise_document_metrics']}




