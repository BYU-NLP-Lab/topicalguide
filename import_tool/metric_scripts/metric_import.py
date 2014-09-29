from __future__ import print_function

import os
import sys
import codecs
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from django.db import transaction

from topic_modeling.visualize.models import *


# Add metric methods
def run_dataset_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the dataset metric."""
    names = metric_module.metric_names_generated(dataset_name)
    dataset = Dataset.objects.using(database_id).get(name=dataset_name)
    for name in names:
        metric, _ = DatasetMetric.objects.using(database_id).get_or_create(name=name)
        if not DatasetMetricValue.objects.using(database_id).filter(metric=metric, dataset=dataset).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, dataset)

def run_document_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the document metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if not DocumentMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, dataset_name, analysis_name)

def run_analysis_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the analysis metric."""
    names = metric_module.metric_names_generated(analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        metric, _ = AnalysisMetric.objects.using(database_id).get_or_create(name=name)
        if not AnalysisMetricValue.objects.using(database_id).filter(metric=metric, analysis_id=analysis.id).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, analysis)

def run_topic_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the topic metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if not TopicMetric.objects.using(database_id).filter(name=name, analysis=analysis).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, dataset_name, analysis_name)

def run_document_pairwise_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the document pairwise metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if not PairwiseDocumentMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, dataset_name, analysis_name)

def run_topic_pairwise_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the topic pairwise metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if not PairwiseTopicMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric_module.add_metric(database_id, dataset_name, analysis_name)


# Removal methods
def remove_dataset_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the dataset metric."""
    names = metric_module.metric_names_generated(dataset_name)
    dataset = Dataset.objects.using(database_id).get(name=dataset_name)
    for name in names:
        metric, _ = DatasetMetric.objects.using(database_id).get_or_create(name=name)
        if DatasetMetricValue.objects.using(database_id).filter(metric=metric, dataset=dataset).exists():
            with transaction.atomic(using=database_id):
                DatasetMetricValue.objects.using(database_id).filter(metric=metric, dataset=dataset).delete()

def remove_document_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the document metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if DocumentMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric = DocumentMetric.objects.using(database_id).get(analysis=analysis, name=name)
                DocumentMetricValue.objects.using(database_id).filter(metric=metric).delete()
                metric.delete()

def remove_analysis_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the analysis metric."""
    names = metric_module.metric_names_generated(analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        metric, _ = AnalysisMetric.objects.using(database_id).get_or_create(name=name)
        if AnalysisMetricValue.objects.using(database_id).filter(metric=metric, analysis=analysis).exists():
            with transaction.atomic(using=database_id):
                AnalysisMetricValue.objects.using(database_id).filter(metric=metric, analysis=analysis).delete()

def remove_topic_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the topic metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if TopicMetric.objects.using(database_id).filter(name=name, analysis=analysis).exists():
            with transaction.atomic(using=database_id):
                metric = TopicMetric.objects.using(database_id).get(name=name, analysis=analysis)
                TopicMetricValue.objects.using(database_id).filter(metric=metric).delete()
                metric.delete()

def remove_document_pairwise_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the document pairwise metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if PairwiseDocumentMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric = PairwiseDocumentMetric.objects.using(database_id).get(analysis=analysis, name=name)
                PairwiseDocumentMetricValue.objects.using(database_id).filter(metric=metric).delete()
                metric.delete()

def remove_topic_pairwise_metric(database_id, dataset_name, analysis_name, metric_module):
    """If the metric isn't present, run the topic pairwise metric."""
    names = metric_module.metric_names_generated(dataset_name, analysis_name)
    analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset__name=dataset_name)
    for name in names:
        if PairwiseTopicMetric.objects.using(database_id).filter(analysis=analysis, name=name).exists():
            with transaction.atomic(using=database_id):
                metric = PairwiseTopicMetric.objects.using(database_id).get(analysis=analysis, name=name)
                PairwiseTopicMetricValue.objects.using(database_id).filter(metric=metric).delete()
                metric.delete()

# vim: et sw=4 sts=4
