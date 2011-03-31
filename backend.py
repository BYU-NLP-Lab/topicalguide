#!/usr/bin/python
## -*- coding: utf-8 -*-

# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

# The doit build file for the Topic Browser.
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

import os, sys
import hashlib

from collections import defaultdict
from datetime import datetime
from subprocess import Popen, PIPE

import import_scripts.dataset_import
import import_scripts.analysis_import

from build.common.make_token_file import make_token_file
from build.common.db_cleanup import remove_analysis
from build.common.db_cleanup import remove_dataset
from helper_scripts.name_schemes.tf_itf import TfitfTopicNamer
from helper_scripts.name_schemes.top_n import TopNTopicNamer
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import TopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import DocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import TopicNameScheme

#If this file is invoked directly, pass it in to the doit system for processing.
# TODO(matt): Pretty hackish, but it's a starting place.  This should be
# cleaned up when we have time.

#build = "twitter"
build = "state_of_the_union"
#build = "kcna/kcna"
#build = "congressional_record"

if __name__ == "__main__":
    if not os.path.exists(".dbs"): os.mkdir(".dbs")
    sys.path.append("tools/doit")
    from doit.doit_cmd import cmd_main
    path = os.path.abspath(sys.argv[0])

    #The database file where we'll store info about this build
    db_name = ".dbs/{0}.db".format(build.replace('/','_'))

    args = ['-f', path] + ['--db', db_name] + sys.argv[1:]
    sys.exit(cmd_main(args))

filename = "build/{0}.py".format(build)
ast = compile(open(filename).read(), filename, 'exec')
eval(ast, globals(), locals())
# Variables and Paths

# This variable should be with Mallet, but it is needed to name the analysis,
# so we have it up here.
if 'num_topics' not in locals():
    num_topics = 20

if 'dataset_name' not in locals():
    dataset_name = "dummy"
if 'dataset_description' not in locals():
    dataset_description = "Dummy dataset"
if 'analysis_name' not in locals():
    analysis_name = "lda{0}topics".format(num_topics)
if 'analysis_description' not in locals():
    analysis_description = "Mallet LDA with {0} topics".format(num_topics)

if 'base_dir' not in locals():
    base_dir = os.curdir
if 'datasets_dir' not in locals():
    datasets_dir = base_dir + "/datasets"
if 'dataset_dir' not in locals():
    dataset_dir = "{0}/{1}".format(datasets_dir, dataset_name)
if 'files_dir' not in locals():
    files_dir = dataset_dir + "/files"
if 'token_regex' not in locals():
    token_regex = r'[A-Za-z]+'

# Mallet
if 'mallet' not in locals():
    mallet = base_dir + "/tools/mallet/mallet"
if 'mallet_input_file_name' not in locals():
    mallet_input_file_name = "mallet_input.txt"
if 'mallet_input' not in locals():
    mallet_input = "{0}/{1}".format(dataset_dir, mallet_input_file_name)
if 'mallet_imported_data' not in locals():
    mallet_imported_data = dataset_dir + "/imported_data.mallet"
if 'mallet_output_gz' not in locals():
    mallet_output_gz = "{0}/{1}.outputstate.gz".format(dataset_dir, analysis_name)
if 'mallet_output' not in locals():
    mallet_output = "{0}/{1}.outputstate".format(dataset_dir, analysis_name)
if 'mallet_doctopics_output' not in locals():
    mallet_doctopics_output = "{0}/{1}.doctopics".format(dataset_dir, analysis_name)
if 'mallet_optimize_interval' not in locals():
    mallet_optimize_interval = 10
if 'mallet_num_iterations' not in locals():
    mallet_num_iterations = 1000

# For dynamically generated attributes file, define task_attributes_file with
# targets [attributes_file]
if 'attributes_file' not in locals():
    attributes_file = dataset_dir + "/attributes.json"
if 'markup_dir' not in locals():
    markup_dir = "{0}/{1}-markup".format(dataset_dir, analysis_name)

# Metrics
# See the documentation or look in metric_scripts for a complete list of
# available metrics
if 'topic_metrics' not in locals():
    topic_metrics = ["token count", "type count", "document entropy",
            "word entropy"]
if 'topic_metric_args' in locals():
    tmp_topic_metric_args = defaultdict(dict)
    tmp_topic_metric_args.update(topic_metric_args)
    topic_metric_args = tmp_topic_metric_args
else:
    topic_metric_args = defaultdict(dict)
if 'pairwise_topic_metrics' not in locals():
    pairwise_topic_metrics = ["document correlation", "word correlation"]
if 'pairwise_topic_metric_args' in locals():
    tmp_pairwise_topic_metric_args = defaultdict(dict)
    tmp_pairwise_topic_metric_args.update(pairwise_topic_metric_args)
    pairwise_topic_metric_args = tmp_pairwise_topic_metric_args
else:
    pairwise_topic_metric_args = defaultdict(dict)
if 'cooccurrence_counts' in locals():
    topic_metrics.append('coherence')
    topic_metric_args['coherence'].update(
            {'counts': cooccurrence_counts})
    pairwise_topic_metrics.append('pairwise coherence')
    pairwise_topic_metric_args['pairwise coherence'].update(
            {'counts': cooccurrence_counts})
if 'document_metrics' not in locals():
    document_metrics = ['token count', 'type count', 'topic entropy']
if 'pairwise_document_metrics' not in locals():
    pairwise_document_metrics = ['word correlation', 'topic correlation']
if 'name_schemes' not in locals():
    name_schemes = [
               TopNTopicNamer(dataset_name, analysis_name, 3),
#               TfitfTopicNamer(dataset_name, analysis_name, 5)
               ]

# Graph-based Visualization
if 'java_base' not in locals():
    java_base = base_dir + "/java"
if 'java_bin' not in locals():
    java_bin = java_base + "/bin"
if 'graph_builder_class' not in locals():
    graph_builder_class = "edu.byu.nlp.topicvis.TopicMapGraphBuilder"
if 'graphs_min_value' not in locals():
    graphs_min_value = 1
if 'graphs_pairwise_metric' not in locals():
    graphs_pairwise_metric = "Document Correlation"
if 'yamba_file' not in locals():
    yamba_file = base_dir + "/yamba"
if not os.path.exists(yamba_file):
    print "Initializing database..."
    os.system("python topic_modeling/manage.py syncdb --noinput > /dev/null")

print "----- Topical Guide Data Import System -----"
print "Dataset name: " + dataset_name

if not os.path.exists(dataset_dir): os.mkdir(dataset_dir)

def cmd_output(cmd):
    return Popen(cmd, shell=True, bufsize=512, stdout=PIPE).stdout.read()

def directory_timestamp(dir):
    return str(os.path.getmtime(dir))

def hash(txt):
    hasher = hashlib.md5()
    hasher.update(txt)
    return hasher.hexdigest()

def directory_recursive_hash(dir):
    if not os.path.exists(dir): return "0"
    return hash(cmd_output("find {dir} -type f -print0 | xargs -0 md5sum".format(dir=dir)))

#If no existing attributes task exists, and if suppress_default_attributes_task is not set to True,
#then define a default attributes task that generates an empty attributes file
#TODO(josh): make the attributes file optional for the import scripts
if not 'task_attributes' in locals() and not ('suppress_default_attributes_task' in locals() and locals()['suppress_default_attributes_task']):
    def make_attributes():
        attrs = open(attributes_file, "w")
        attrs.write('[')
        for filename in os.listdir(files_dir):
            attrs.write('{"attributes": {}, "path": "' + filename + '"}')
        attrs.write(']')

    def task_attributes():
        task = dict()
        task['targets'] = [attributes_file]
        task['actions'] = [(make_attributes)]
        return task

if 'task_mallet_input' not in locals():
    def task_mallet_input():
        task = dict()
        task['targets'] = [mallet_input]
        task['actions'] = [(make_token_file, [files_dir, mallet_input])]
        task['clean']   = ["rm -f "+mallet_input]
        if 'task_extract_data' in globals():
            task['task_dep'] = ['extract_data']
        task['uptodate'] = [os.path.exists(mallet_input)]
#        task['file_dep'] = [files_dir]
        return task

if 'task_mallet_imported_data' not in locals():
    def task_mallet_imported_data():
        task = dict()
        task['targets'] = [mallet_imported_data]
        cmd = '{0} import-file --input {1} --output {2} --keep-sequence --set-source-by-name --remove-stopwords'.format(mallet, mallet_input, mallet_imported_data)
        if token_regex is not None:
            cmd += " --token-regex " + token_regex
        task['actions'] = [cmd]
        task['file_dep'] = [mallet_input]
        task['clean'] = ["rm -f " + mallet_imported_data]
        return task

if 'task_mallet_output_gz' not in locals():
    def task_mallet_output_gz():
        task = dict()
        task['targets'] = [mallet_output_gz, mallet_doctopics_output]
        task['actions'] = ['{0} train-topics --input {1} --optimize-interval {2} --num-iterations {3} --num-topics {4} --output-state {5} --output-doc-topics {6}'
                   .format(mallet, mallet_imported_data, mallet_optimize_interval, mallet_num_iterations, num_topics, mallet_output_gz, mallet_doctopics_output)]
        task['file_dep'] = [mallet_imported_data]
        task['clean'] = ["rm -f " + mallet_output_gz,
                 "rm -f " + mallet_doctopics_output]
        return task

if 'task_mallet_output' not in locals():
    def task_mallet_output():
        task = dict()
        task['targets'] = [mallet_output]
        task['actions'] = ["zcat {0} > {1}".format(mallet_output_gz, mallet_output)]
        task['file_dep'] = [mallet_output_gz]
        task['clean'] = ["rm -f " + mallet_output]
        return task

if 'task_mallet' not in locals():
    def task_mallet():
        return {'actions':None, 'task_dep': ['mallet_input', 'mallet_imported_data', 'mallet_output_gz', 'mallet_output']}

if 'task_dataset_import' not in locals():
    def task_dataset_import():
        def dataset_in_database():
            try:
                Dataset.objects.get(name=dataset_name)
                print 'dataset ' + dataset_name + ' in database'
                return True
            except Dataset.DoesNotExist:
                print 'dataset ' + dataset_name + ' NOT in database'
                return False
        # TODO(matt): clean up and possibly rename dataset_import.py and
        # analysis_import.py, now that we are using this build script - we don't
        #  need standalone scripts anymore for that stuff
        task = dict()
        task['actions'] = [(import_scripts.dataset_import.main, [mallet_output, dataset_name, attributes_file, dataset_dir, files_dir, dataset_description])]
        task['file_dep'] = [mallet_output, attributes_file, yamba_file]
        task['clean'] = [(remove_dataset, [dataset_name])]
        task['uptodate'] = [dataset_in_database()]
        return task

if 'task_analysis_import' not in locals():
    def task_analysis_import():
        def analysis_in_database():
            try:
                d = Dataset.objects.get(name=dataset_name)
                Analysis.objects.get(dataset=d, name=analysis_name)
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist):
                return False
        task = dict()
        task['actions'] = [(import_scripts.analysis_import.main, [dataset_name, attributes_file, analysis_name, analysis_description, mallet_output, mallet_input, files_dir, token_regex])]
        task['file_dep'] = [mallet_output, mallet_input, attributes_file]
        task['clean'] = [
            (remove_analysis, [dataset_name, analysis_name]),
            "rm -rf {0}".format(markup_dir)
        ]
        task['task_dep'] = ['dataset_import']
        task['uptodate'] = [analysis_in_database()]
        return task

if 'task_name_schemes' not in locals():
    def task_name_schemes():
        def scheme_in_database(ns):
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                TopicNameScheme.objects.get(analysis=analysis, name=ns.scheme_name())
                return True
            except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicNameScheme.DoesNotExist):
                return False
        def generate_names(ns):
            ns.name_all_topics()
        def clean_names(ns):
            ns.unname_all_topics()

        print "Available topic name schemes: " + u', '.join([ns.scheme_name() for ns in name_schemes])
        for ns in name_schemes:
            task = dict()
            task['name'] = ns.scheme_name()
            task['actions'] = [(generate_names, [ns])]
            task['task_dep'] = ['analysis_import']
            task['clean'] = [(clean_names,[ns])]
            task['uptodate'] = [scheme_in_database(ns)]
            yield task

if 'task_topic_metrics' not in locals():
    def task_topic_metrics():
        from metric_scripts.topics import metrics

        def metric_in_database(topic_metric):
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset,
                        name=analysis_name)
                names = metrics[topic_metric].metric_names_generated(
                        dataset_name, analysis_name)
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
                metrics[topic_metric].add_metric(dataset_name, analysis_name,
                        **topic_metric_args[topic_metric])
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
            dataset = Dataset.objects.get(name=dataset_name)
            analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
            names = metrics[topic_metric].metric_names_generated(dataset_name,
                    analysis_name)
            for topic_metric_name in names:
                TopicMetric.objects.get(analysis=analysis,
                        name=topic_metric_name).delete()

        print "Available topic metrics: " + u', '.join(topic_metrics)
        for topic_metric in topic_metrics:
            task = dict()
            task['name'] = topic_metric.replace(' ', '_')
            task['actions'] = [(import_metric, [topic_metric])]
            task['clean'] = ["ls", (clean_metric, [topic_metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [metric_in_database(topic_metric)]
            yield task

if 'task_pairwise_topic_metrics' not in locals():
    def task_pairwise_topic_metrics():
        from metric_scripts.topics import pairwise_metrics

        def metric_in_database(metric):
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset,
                        name=analysis_name)
                names = pairwise_metrics[metric].metric_names_generated(
                        dataset_name, analysis_name)
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
                pairwise_metrics[metric].add_metric(dataset_name, analysis_name)
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
            dataset = Dataset.objects.get(name=dataset_name)
            analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
            names = pairwise_metrics[metric].metric_names_generated(
                    dataset_name, analysis_name)
            for metric_name in names:
                PairwiseTopicMetric.objects.get(analysis=analysis,
                        name=metric_name).delete()

        print "Available pairwise topic metrics: " + u', '.join(
                pairwise_topic_metrics)
        for pairwise_topic_metric in pairwise_topic_metrics:
            task = dict()
            task['name'] = pairwise_topic_metric.replace(' ', '_')
            task['actions'] = [(import_metric, [pairwise_topic_metric])]
            task['clean'] = [(clean_metric, [pairwise_topic_metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [metric_in_database(pairwise_topic_metric)]
            yield task

if 'task_document_metrics' not in locals():
    def task_document_metrics():
        from metric_scripts.documents import metrics

        def metric_in_database(metric):
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                names = metrics[metric].metric_names_generated(dataset_name, analysis_name)
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
                metrics[metric].add_metric(dataset_name, analysis_name)
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
            dataset = Dataset.objects.get(name=dataset_name)
            analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
            names = metrics[metric].metric_names_generated(dataset_name, analysis_name)
            for metric_name in names:
                metric = DocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()

        print "Available document metrics: " + u', '.join(metrics)
        for metric in metrics:
            task = dict()
            task['name'] = metric.replace(' ', '_')
            task['actions'] = [(import_metric, [metric])]
            task['clean'] = ["ls", (clean_metric, [metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [metric_in_database(metric)]
            yield task

if 'task_pairwise_document_metrics' not in locals():
    def task_pairwise_document_metrics():
        from metric_scripts.documents import pairwise_metrics

        def metric_in_database(metric):
            try:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                names = pairwise_metrics[metric].metric_names_generated(dataset_name, analysis_name)
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
                pairwise_metrics[metric].add_metric(dataset_name, analysis_name)
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
            dataset = Dataset.objects.get(name=dataset_name)
            analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
            names = pairwise_metrics[metric].metric_names_generated(dataset_name, analysis_name)
            if isinstance(names, basestring): names = [names]
            for metric_name in names:
                PairwiseDocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()

        print "Available pairwise document metrics: " + u', '.join(pairwise_metrics)
        for metric in pairwise_document_metrics:
            task = dict()
            task['name'] = metric.replace(' ', '_')
            task['actions'] = [(import_metric, [metric])]
            task['clean'] = [(clean_metric, [metric])]
            task['task_dep'] = ['analysis_import']
            task['uptodate'] = [metric_in_database(metric)]
            yield task

if 'task_metrics' not in locals():
    def task_metrics():
        return {'actions':None, 'task_dep': ['analysis_import', 'topic_metrics', 'pairwise_topic_metrics', 'document_metrics', 'pairwise_document_metrics']}

def task_hash_java():
    return {'actions': [(directory_recursive_hash, [java_base])]}

if 'task_compile_java' not in locals():
    def task_compile_java():
        actions = ["cd {0} && ant -lib lib".format(java_base)]
        result_deps = ['hash_java']
        clean = ['rm -rf ' + java_bin]
        return {'actions':actions, 'result_dep':result_deps, 'clean':clean}

if 'task_graphs' not in locals():
    def task_graphs():
        for ns in name_schemes:
            task = dict()
            graphs_img_dir = "{0}/topic_maps/{1}/{2}".format(dataset_dir, analysis_name, ns.scheme_name())
            graphs_unlinked_img_dir = graphs_img_dir + "-unlinked"
            gexf_file_name = "{0}/full_graph.gexf".format(graphs_img_dir)
            
            task['actions'] = [
                'java -cp {0}:{1}/lib/gephi-toolkit.jar:{1}/lib/statnlp-rev562.jar:{1}/lib/sqlitejdbc-v056.jar {2} {3} {4} {5} {6} "{7}" {8} {9} {10} {11}'
                .format(java_bin,java_base,graph_builder_class,graphs_min_value,dataset_name,analysis_name,ns.scheme_name(),graphs_pairwise_metric, yamba_file, graphs_unlinked_img_dir, graphs_img_dir, gexf_file_name)
            ]
            task['task_dep'] = ['pairwise_topic_metrics', 'name_schemes', 'compile_java']
            task['clean'] =  [
                'rm -rf '+graphs_unlinked_img_dir,
                'rm -rf '+graphs_img_dir
            ]
            task['name'] = ns.scheme_name()
            task['uptodate'] = [os.path.exists(graphs_img_dir)]
            yield task
#
#def task_reset_db():
#    actions = ['yes "yes" | python topic_modeling/manage.py reset visualize']
#    return {'actions':actions}
