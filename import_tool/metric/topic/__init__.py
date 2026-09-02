from collections import OrderedDict
from visualize.models import TopicMetricValue
from . import token_count
from . import type_count
from . import document_entropy
from . import word_entropy

database_table = TopicMetricValue
metrics = OrderedDict([
    ('token_count', token_count),
    ('type_count', type_count),
    ('document_entropy', document_entropy),
    ('word_entropy', word_entropy),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return TopicMetricValue.objects.using(database_id).filter(topic__analysis=analysis_db, metric=metric_db).exists()
