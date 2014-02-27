#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

# general utilities
import os
import sys
import codecs
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from dataset_classes.generic_dataset import GenericDataset

from topic_modeling.visualize.models import (Dataset, TopicMetric,
    PairwiseTopicMetric, DocumentMetric, PairwiseDocumentMetric, 
    TopicNameScheme)
from topic_modeling.visualize.models import (Analysis, DatasetMetric,
    AnalysisMetric, DatasetMetricValue, AnalysisMetricValue,
    DatasetMetaInfoValue, DocumentMetaInfoValue, WordTypeMetaInfoValue,
    WordTokenMetaInfoValue, AnalysisMetaInfoValue, TopicMetaInfoValue,
    WordType, WordToken, Document, Topic, PairwiseTopicMetricValue,
    DocumentMetricValue)

# TODO the following methods don't have a way to cleanup if an error is thrown
# TODO the following methods are poorly documented and need additional explaination
# TODO the following methods import their own 'metrics' object all from different sources
#       which is bad, is there a way to refactor that?

def dataset_metric_in_database(metric_name, metrics, dataset_name, analysis_name):
    '''\
    Helper function fo dataset_metrics().
    '''
    for name in metrics[metric_name].metric_names_generated(dataset_name):
        try:
            DatasetMetricValue.objects.get(metric__name=name, dataset__name=dataset_name)
        except DatasetMetricValue.DoesNotExist:
            return False
    return True

def dataset_import_metric(dataset_metric, metrics, dataset_name, analysis_name):
    '''\
    Helper function for dataset_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % dataset_metric)
    sys.stdout.flush()

    dataset_ = Dataset.objects.get(name=dataset_name)

    try:
        metrics[dataset_metric].add_metric(dataset_)
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()

def dataset_metrics(dataset_name, analysis_name):
    '''\
    Runs metrics on the dataset. This wraps metrics from the helper_scripts.
    '''
    from metric_scripts.datasets import metrics
    for metric_name in metrics:
        if not dataset_metric_in_database(metric_name.replace(' ', '_').split(':')[-1], metrics, dataset_name, analysis_name):
            dataset_import_metric(metric_name, metrics, dataset_name, analysis_name)



       
def analysis_metric_in_database(metric_name, metrics, dataset_name, analysis_name):
    '''\
    Helper function to analysis_metrics().
    '''
    for name in metrics[metric_name].metric_names_generated(analysis_name):
        try:
            AnalysisMetricValue.objects.get(metric__name=name, analysis__name=analysis_name)
        except AnalysisMetricValue.DoesNotExist:
            return False
    return True

def analysis_import_metric(analysis_metric, metrics, dataset_name, analysis_name, analysis_db):
    '''\
    Helper function to analysis_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % analysis_metric,)
    sys.stdout.flush()

    try:
        metrics[analysis_metric].add_metric(analysis_db)
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()

def analysis_metrics(dataset_name, analysis_name, analysis_db):
    from metric_scripts.analyses import metrics
    for metric_name in metrics:
        if not analysis_metric_in_database(metric_name.replace(' ', '_').split(':')[-1], 
                                           metrics, dataset_name, analysis_name):
            analysis_import_metric(metric_name, metrics, dataset_name, analysis_name, analysis_db)





def topic_metric_in_database(topic_metric, metrics, dataset_name, analysis_name, analysis_db):
    '''\
    Helper function to topic_metrics().
    '''
    # TODO see if there is a way to refactor so we don't have to use this kludge
    def analysis():
        return analysis_db
    
    try:
        names = metrics[topic_metric].metric_names_generated(dataset_name, analysis_name)
        for name in names:
            TopicMetric.objects.get(analysis=analysis, name=name)
        return True
    except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicMetric.DoesNotExist):
        return False

def topic_import_metric(topic_metric, metrics, dataset_name, analysis_name, topic_metric_args):
    '''\
    Helper function to topic_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % topic_metric)
    sys.stdout.flush()
    try:
        metrics[topic_metric].add_metric(dataset_name, analysis_name,
                **topic_metric_args[topic_metric])
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()

def topic_metrics(topic_metrics, dataset_name, analysis_name, analysis_db, topic_metric_args):
    from metric_scripts.topics import metrics
    for topic_metric in topic_metrics:
        if not topic_metric_in_database(topic_metric, metrics, dataset_name, analysis_name, analysis_db):
            topic_import_metric(topic_metric, metrics, dataset_name, analysis_name, topic_metric_args)





def pairwise_topic_metric_in_database(metric_name, metrics, dataset_name, analysis_name, analysis_db):
    '''\
    Helper function fo pairwise_topic_metrics().
    '''
    # TODO see if there is a way to refactor so we don't have to use this kludge
    def analysis():
        return analysis_db
    
    try:
        names = metrics[metric_name].metric_names_generated(
                dataset_name, analysis_name)
        for name in names:
            metric_name = PairwiseTopicMetric.objects.get(analysis=analysis,
                        name=name)
            values = PairwiseTopicMetricValue.objects.filter(metric=metric_name)
            if not values.count():
                return False
        return True
    except (Dataset.DoesNotExist, Analysis.DoesNotExist,
            PairwiseTopicMetric.DoesNotExist):
        return False

def pairwise_topic_import_metric(dataset_metric, metrics, dataset_name, analysis_name):
    '''\
    Helper function for pairwise_topic_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % dataset_metric)
    sys.stdout.flush()
    try:
        print('yeah...')
        metrics[dataset_metric].add_metric(dataset_name, analysis_name)
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()

def pairwise_topic_metrics(pairwise_topic_metrics, dataset_name, analysis_name, analysis_db):
    from metric_scripts.topics.pairwise import metrics
    for pairwise_topic_metric in pairwise_topic_metrics:
        if not pairwise_topic_metric_in_database(pairwise_topic_metric.replace(' ', '_').split(':')[-1], metrics, dataset_name, analysis_name, analysis_db):
            pairwise_topic_import_metric(pairwise_topic_metric, metrics, dataset_name, analysis_name)




def document_metric_in_database(metric_name, metrics, dataset_name, analysis_name, analysis_db):
    '''\
    Helper function fo document_metrics().
    '''
    # TODO see if there is a way to refactor so we don't have to use this kludge
    def analysis():
        return analysis_db
    
    try:
        names = metrics[metric_name].metric_names_generated(dataset_name, analysis_name)
        for name in names:
            metric_name = DocumentMetric.objects.get(analysis=analysis, name=name)
            if not DocumentMetricValue.objects.filter(metric=metric_name).count():
                return False
        return True
    except (Dataset.DoesNotExist, Analysis.DoesNotExist, DocumentMetric.DoesNotExist):
        return False

def document_import_metric(dataset_metric, metrics, dataset_name, analysis_name):
    '''\
    Helper function for document_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % dataset_metric)
    sys.stdout.flush()
    try:
        metrics[dataset_metric].add_metric(dataset_name, analysis_name)
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()
    
def document_metrics(dataset_name, analysis_name, analysis_db):
    from metric_scripts.documents import metrics
    for metric in metrics:
        if not document_metric_in_database(metric, metrics, dataset_name, analysis_name, analysis_db):
            document_import_metric(metric, metrics, dataset_name, analysis_name)




def pairwise_document_metric_in_database(metric_name, metrics, dataset_name, analysis_name, analysis_db):
    '''\
    Helper function fo pairwise_document_metrics().
    '''
    # TODO see if there is a way to refactor so we don't have to use this kludge
    def analysis():
        return analysis_db
    
    try:
        names = metrics[metric_name].metric_names_generated(dataset_name, analysis_name)
        for name in names:
            metric_name = PairwiseDocumentMetric.objects.get(analysis=analysis, name=name)
            if not PairwiseTopicMetricValue.objects.filter(metric=metric_name).count():
                return False
        return True
    except (Dataset.DoesNotExist, Analysis.DoesNotExist, PairwiseDocumentMetric.DoesNotExist):
        return False

def pairwise_document_import_metric(dataset_metric, metrics, dataset_name, analysis_name):
    '''\
    Helper function for pairwise_document_metrics().
    '''
    start_time = datetime.datetime.now()
    print('Adding %s...' % dataset_metric)
    sys.stdout.flush()
    try:
        metrics[dataset_metric].add_metric(dataset_name, analysis_name)
        end_time = datetime.datetime.now()
        print('  Done', end_time - start_time)
        sys.stdout.flush()
    except KeyError as e:
        print("\nI couldn't find the metric you specified:", e)
        sys.stdout.flush()
    except RuntimeError as e:
        print("\nThere was an error importing the specified metric:", e)
        sys.stdout.flush()

def pairwise_document_metrics(pairwise_document_metrics, dataset_name, analysis_name, analysis_db):
    from metric_scripts.documents.pairwise import metrics
    for metric in pairwise_document_metrics:
        if not pairwise_document_metric_in_database(metric, metrics, dataset_name, analysis_name, analysis_db):
            pairwise_document_import_metric(metric, metrics, dataset_name, analysis_name)


# vim: et sw=4 sts=4
