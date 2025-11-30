from collections import OrderedDict
from visualize.models import TopicPairwiseMetricValue
from . import document_correlation
from . import word_correlation
from . import embedding_distance
#~ from . import coherence

database_table = TopicPairwiseMetricValue
metrics = OrderedDict([
    ('document_correlation', document_correlation),
    ('word_correlation', word_correlation),
    ('embedding_distance', embedding_distance),
    #~ ('coherence', coherence),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return TopicPairwiseMetricValue.objects.using(database_id).filter(origin_topic__analysis=analysis_db, metric=metric_db).exists()
