from visualize.models import DatasetMetricValue
from collections import OrderedDict
from . import document_count

database_table = DatasetMetricValue
metrics = OrderedDict([
    ('document_count', document_count),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return DatasetMetricValue.objects.using(database_id).filter(dataset=dataset_db, metric=metric_db).exists()
