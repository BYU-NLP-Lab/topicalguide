from collections import OrderedDict
from visualize.models import DocumentAnalysisMetricValue
from . import token_count
from . import type_count
from . import topic_entropy

database_table = DocumentAnalysisMetricValue
metrics = OrderedDict([
    ('token_count', token_count),
    ('type_count', type_count),
    ('topic_entropy', topic_entropy),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return DocumentAnalysisMetricValue.objects.using(database_id).filter(analysis=analysis_db, metric=metric_db).exists()
