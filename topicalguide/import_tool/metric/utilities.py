from __future__ import division, print_function, unicode_literals
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from django.db import transaction
from visualize.models import *


def get_metric_names(database_id):
    """Return a dict mapping metric names to Metric database objects.
    database_id -- the dict key specifying the database in Django
    """
    return {metric.name: metric for metric in Metric.objects.using(database_id).all()}

def run_metric(database_id, dataset_db, analysis_db, metrics_db, database_table, metric_module, metric_exists_function):
    """Run the metric defined in the given module on the analysis and/or dataset.
    Import the results into the database.
    database_id -- the dict key specifying the database in Django
    dataset_db -- a Dataset Django database object
    anlaysis_db -- an Analysis Django database object
    metrics_db -- what is returned by get_metric_names
    database_table -- the Django class corresponding to the metric_module
    metric_module -- the python module containing the metric function
    metric_exists_function -- the function that determines if the metric has already been computed
    """
    metric_name = metric_module.metric_name
    if metric_name not in metrics_db:
        metrics_db[metric_name] = Metric.objects.using(database_id).create(name=metric_name)
    
    if not metric_exists_function(database_id, dataset_db, analysis_db, metrics_db[metric_name]):
        with transaction.atomic(using=database_id):
            metrics_to_commit = []
            metric_db = metrics_db[metric_name]
            for result in metric_module.compute_metric(database_id, dataset_db, analysis_db):
                result['metric'] = metric_db
                metrics_to_commit.append(database_table(**result))
            database_table.objects.using(database_id).bulk_create(metrics_to_commit)
    else:
        print('Metric %s is already finished.'%(metric_name,))
