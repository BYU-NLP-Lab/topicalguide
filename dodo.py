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
# You can either invoke this file directly (./dodo.py) or install doit and run
# `doit` in the same directory as this file
#
# Useful commands:
#  dodo.py list #Lists the available top-level tasks (sub-tasks are not displayed)
#  dodo.py #Builds everything!
#  dodo.py clean -c mallet #Cleans the mallet files
#  dodo.py metrics #Computes all metrics
#  dodo.py topic_metrics #Computes just the topic metrics
#  dodo.py topic_metrics:document_entropy #Computes just the document entropy topic metric
#  dodo.py clean topic_metrics:document_entropy #Cleans just the document entropy topic metric
#
#NOTE: probably necessary to do 'dodo.py forget' when switching between datasets/analyses.
#TODO:
#  Allow specification of multiple num_topics
#

import os, sys
import hashlib
from subprocess import Popen, PIPE
from datetime import datetime
from build.common.make_token_file import make_token_file
import import_scripts.dataset_import
import import_scripts.analysis_import
from build.common.db_cleanup import remove_dataset, remove_analysis
from topic_modeling.visualize.models import Analysis, Dataset, TopicMetric, PairwiseTopicMetric, DocumentMetric, PairwiseDocumentMetric
from helper_scripts.name_schemes.tf_itf import TfitfTopicNamer
from helper_scripts.name_schemes.top_n import TopNTopicNamer

#If this file is invoked directly, pass it in to the doit system for processing.
# TODO(matt): Pretty hackish, but it's a starting place.  This should be
# cleaned up when we have time.
if __name__ == "__main__":
    sys.path.append("tools/doit")
    from doit.doit_cmd import cmd_main
    sys.exit(cmd_main(sys.argv[1:]))

build = "state_of_the_union"
#build = "congressional_record"
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

#For dynamically generated attributes file, define task_attributes_file with targets [attributes_file]
if 'attributes_file' not in locals():
    attributes_file = dataset_dir + "/attributes.json"
if 'markup_dir' not in locals():
    markup_dir = "{0}/{1}-markup".format(dataset_dir, analysis_name)

#Metrics
# TODO(matt): can we make this dynamic?
# TODO(matt): look at metric_scripts/topics/__init__.py for the "all" list,
# and for each metric target
# TODO(matt): have a "minimal" or "default" target that is the default if the
# dataset file doesn't specify one
# Same thing with document metrics (and word metrics, when we add them)
if 'topic_metrics' not in locals():
    topic_metrics = ["token count", "type count", "document entropy", "word entropy"]
if 'pairwise_topic_metrics' not in locals():
    pairwise_topic_metrics = ["document correlation", "word correlation"]
if 'document_metrics' not in locals():
    document_metrics = ['token count', 'type count', 'topic entropy']
if 'pairwise_document_metrics' not in locals():
    pairwise_document_metrics = ['word correlation','topic correlation']
if 'name_schemes' not in locals():
    name_schemes = [
               TopNTopicNamer(dataset_name, analysis_name, 2),
#               TfitfTopicNamer(dataset_name, analysis_name, 5)
               ]

#Graph-based Visualization
if 'java_base' not in locals():
    java_base = base_dir + "/java"
if 'java_bin' not in locals():
    java_bin = java_base + "/bin"
if 'graph_builder_class' not in locals():
    graph_builder_class="edu.byu.nlp.topicvis.TopicMapGraphBuilder"
if 'graphs_min_value' not in locals():
    graphs_min_value = 1
if 'graphs_base_url' not in locals():
    graphs_base_url = "http://127.0.0.1:8000"
if 'graphs_pairwise_metric' not in locals():
    graphs_pairwise_metric = "Document Correlation"
if 'yamba_file' not in locals():
    yamba_file = base_dir + "/yamba"
if not os.path.exists(yamba_file):
    print "Initializing database..."
    os.system("python topic_modeling/manage.py syncdb --noinput > /dev/null")

print "----- Topic Browser Build System -----"
print "Dataset name: " + dataset_name

if not os.path.exists(dataset_dir): os.mkdir(dataset_dir)
#if not os.path.exists(files_dir): os.mkdir(files_dir)


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

def task_hash_dataset():
    dict = {}
    dict['actions'] = [(directory_timestamp, [files_dir])]
    if 'task_copy_and_transform_dataset' in locals():
        dict['task_dep'] = ['copy_and_transform_dataset']
    return dict

if 'task_mallet_input' not in locals():
    def task_mallet_input():
        targets = [mallet_input]
        actions = [(make_token_file, [files_dir, mallet_input])]
        result_deps = ['hash_dataset']
        clean = ["rm -f "+mallet_input]
        return {'targets':targets, 'actions':actions, 'result_dep':result_deps, 'clean':clean}

if 'task_mallet_imported_data' not in locals():
    def task_mallet_imported_data():
        targets = [mallet_imported_data]
        cmd = '{0} import-file --input {1} --output {2} --keep-sequence --set-source-by-name --remove-stopwords'.format(mallet, mallet_input, mallet_imported_data)
        if token_regex is not None:
            cmd += " --token-regex "+token_regex
        actions = [cmd]
        file_deps = [mallet_input]
        clean = ["rm -f "+mallet_imported_data]
        return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

if 'task_mallet_output_gz' not in locals():
    def task_mallet_output_gz():
        targets = [mallet_output_gz, mallet_doctopics_output]
        actions = ['{0} train-topics --input {1} --optimize-interval {2} --num-iterations {3} --num-topics {4} --output-state {5} --output-doc-topics {6}'
                   .format(mallet, mallet_imported_data, mallet_optimize_interval, mallet_num_iterations, num_topics, mallet_output_gz, mallet_doctopics_output)]
        file_deps = [mallet_imported_data]
        clean = ["rm -f "+mallet_output_gz,
                 "rm -f "+mallet_doctopics_output]
        return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

if 'task_mallet_output' not in locals():
    def task_mallet_output():
        targets = [mallet_output]
        actions = ["zcat {0} > {1}".format(mallet_output_gz,mallet_output)]
        file_deps = [mallet_output_gz]
        clean = ["rm -f "+mallet_output]
        return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

if 'task_mallet' not in locals():
    def task_mallet():
        return {'actions':None, 'task_dep': ['mallet_input', 'mallet_imported_data', 'mallet_output_gz', 'mallet_output']}

if 'task_dataset_import' not in locals():
    def task_dataset_import():
        # TODO(matt): clean up and possibly rename dataset_import.py and
        # analysis_import.py, now that we are using this build script - we don't
        #  need standalone scripts anymore for that stuff
        actions = [(import_scripts.dataset_import.main, [mallet_output, dataset_name, attributes_file, dataset_dir, files_dir, dataset_description])]
        file_deps = [mallet_output, attributes_file, yamba_file]
        clean = [(remove_dataset, [dataset_name])]
        return {'actions':actions, 'file_dep':file_deps, 'clean':clean}

if 'task_analysis_import' not in locals():
    def task_analysis_import():
        actions = [(import_scripts.analysis_import.main, [dataset_name, attributes_file, analysis_name, analysis_description, mallet_output, mallet_input, files_dir, token_regex])]
        file_deps = [mallet_output, mallet_input, attributes_file]
        clean = [
            (remove_analysis, [dataset_name, analysis_name]),
            "rm -rf {0}".format(markup_dir)
        ]
        task_deps = ['dataset_import']
        return {'actions':actions, 'file_dep':file_deps, 'task_dep':task_deps, 'clean':clean}

if 'task_name_schemes' not in locals():
    def task_name_schemes():
        def generate_names(ns):
            ns.name_all_topics()
        def clean_names(ns):
            ns.unname_all_topics()
        
        print "Available topic name schemes: " + u', '.join([ns.scheme_name() for ns in name_schemes])
        for ns in name_schemes:
            actions = [(generate_names,[ns])]
            task_deps = ['analysis_import']
            clean = [(clean_names,[ns])]
            yield {'name':ns.scheme_name(), 'actions':actions, 'task_dep':task_deps, 'clean':clean}

if 'task_topic_metrics' not in locals():
    def task_topic_metrics():
        from metric_scripts.topics import metrics
        def import_metric(topic_metric):
            start_time = datetime.now()
            print 'Adding %s...' % topic_metric,
            sys.stdout.flush()
            try:
                metrics[topic_metric].add_metric(dataset_name, analysis_name)
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
            names = metrics[topic_metric].metric_names_generated(dataset_name, analysis_name)
            if isinstance(names, basestring): names = [names]
            for topic_metric_name in names:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                metric = TopicMetric.objects.get(analysis=analysis, name=topic_metric_name)
                metric.delete()
        
        print "Available topic metrics: " + u', '.join(topic_metrics)
        for topic_metric in topic_metrics:
            actions = [(import_metric, [topic_metric])]
            clean = ["ls", (clean_metric, [topic_metric])]
            task_deps = ['analysis_import']
            yield {'name': topic_metric.replace(' ','_'),'actions':actions, 'task_dep':task_deps, 'clean':clean}
    
if 'task_pairwise_topic_metrics' not in locals():
    def task_pairwise_topic_metrics():
        from metric_scripts.topics import pairwise_metrics
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
            names = pairwise_metrics[metric].metric_names_generated(dataset_name, analysis_name)
            if isinstance(names, basestring): names = [names]
            for metric_name in names:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                PairwiseTopicMetric.objects.get(analysis=analysis, name=metric_name).delete()
        
        print "Available pairwise topic metrics: " + u', '.join(pairwise_metrics)
        for topic_metric in pairwise_metrics:
            actions = [(import_metric, [topic_metric])]
            clean = [(clean_metric, [topic_metric])]
            task_deps = ['analysis_import']
            yield {'name': topic_metric.replace(' ','_'),'actions':actions, 'task_dep':task_deps, 'clean':clean}

if 'task_document_metrics' not in locals():
    def task_document_metrics():
        from metric_scripts.documents import metrics
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
            names = metrics[metric].metric_names_generated(dataset_name, analysis_name)
            if isinstance(names, basestring): names = [names]
            for metric_name in names:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                metric = DocumentMetric.objects.get(analysis=analysis, name=metric_name)
                metric.delete()
        
        print "Available document metrics: " + u', '.join(metrics)
        for metric in metrics:
            actions = [(import_metric, [metric])]
            clean = ["ls", (clean_metric, [metric])]
            task_deps = ['analysis_import']
            yield {'name': metric.replace(' ','_'),'actions':actions, 'task_dep':task_deps, 'clean':clean}

if 'task_pairwise_document_metrics' not in locals():
    def task_pairwise_document_metrics():
        from metric_scripts.documents import pairwise_metrics
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
            names = pairwise_metrics[metric].metric_names_generated(dataset_name, analysis_name)
            if isinstance(names, basestring): names = [names]
            for metric_name in names:
                dataset = Dataset.objects.get(name=dataset_name)
                analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
                PairwiseDocumentMetric.objects.get(analysis=analysis, name=metric_name).delete()
        
        print "Available pairwise document metrics: " + u', '.join(pairwise_metrics)
        for metric in pairwise_metrics:
            actions = [(import_metric, [metric])]
            clean = [(clean_metric, [metric])]
            task_deps = ['analysis_import']
            yield {'name': metric.replace(' ','_'),'actions':actions, 'task_dep':task_deps, 'clean':clean}

if 'task_metrics' not in locals():
    def task_metrics():
        return {'actions':None, 'task_dep': ['analysis_import', 'topic_metrics','pairwise_topic_metrics','document_metrics','pairwise_document_metrics']}

def task_hash_java():
    return {'actions': [(directory_recursive_hash, [java_base])]}

if 'task_java' not in locals():
    def task_java():
        actions = ["cd {0} && ant -lib lib".format(java_base)]
        result_deps = ['hash_java']
        clean = ['rm -rf '+java_bin]
        return {'actions':actions, 'result_dep':result_deps, 'clean':clean}

if 'task_graphs' not in locals():
    def task_graphs():
        for ns in name_schemes:
            graphs_img_dir = "{0}/topic_maps/{1}/{2}".format(dataset_dir, analysis_name, ns.scheme_name())
            graphs_unlinked_img_dir = graphs_img_dir + "-unlinked"
            gexf_file_name = "{0}/full_graph.gexf".format(graphs_img_dir)
            
            actions = [
                'java -cp {0}:{1}/lib/gephi-toolkit.jar:{1}/lib/statnlp-rev562.jar:{1}/lib/sqlitejdbc-v056.jar {2} {3} {4} {5} {6} {7} "{8}" {9} {10} {11} {12}'
                .format(java_bin,java_base,graph_builder_class,graphs_min_value,graphs_base_url,dataset_name,analysis_name,ns.scheme_name(),graphs_pairwise_metric, yamba_file, graphs_unlinked_img_dir, graphs_img_dir, gexf_file_name)
            ]
            task_deps = ['pairwise_topic_metrics', 'name_schemes', 'java']
            result_deps = ['hash_java']
            clean =  [
                'rm -rf '+graphs_unlinked_img_dir,
                'rm -rf '+graphs_img_dir
            ]
            yield {'name':ns.scheme_name(), 'actions':actions, 'task_dep':task_deps, 'result_dep':result_deps, 'clean':clean}
#
#def task_reset_db():
#    actions = ['yes "yes" | python topic_modeling/manage.py reset visualize']
#    return {'actions':actions}
