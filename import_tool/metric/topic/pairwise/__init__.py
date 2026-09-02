from collections import OrderedDict
from visualize.models import TopicPairwiseMetricValue
from . import document_correlation
from . import word_correlation
from . import embedding_distance

# coherence was commented out here and has been removed for the same reasons as
# its topic-level counterpart -- see the note in ../__init__.py and TASKS.md 0.4.

database_table = TopicPairwiseMetricValue
metrics = OrderedDict([
    ('document_correlation', document_correlation),
    ('word_correlation', word_correlation),
    ('embedding_distance', embedding_distance),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return TopicPairwiseMetricValue.objects.using(database_id).filter(origin_topic__analysis=analysis_db, metric=metric_db).exists()
