from collections import OrderedDict
from visualize.models import TopicMetricValue
from . import token_count
from . import type_count
from . import document_entropy
from . import word_entropy

# alpha, attribute_entropy, coherence, sentiment, subset_document_entropy and
# subset_token_count were commented out here for years and have been removed.
# They used the pre-4.2 add_metric() protocol and models that no longer exist
# (TopicMetric, topic.topicword_set, word.ngram); coherence also needed an
# external co-occurrence database that is not in this repository. Reviving any
# of them means reimplementing against compute_metric() and the current schema
# -- see TASKS.md 0.4. Recover the originals from git history if useful.

database_table = TopicMetricValue
metrics = OrderedDict([
    ('token_count', token_count),
    ('type_count', type_count),
    ('document_entropy', document_entropy),
    ('word_entropy', word_entropy),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return TopicMetricValue.objects.using(database_id).filter(topic__analysis=analysis_db, metric=metric_db).exists()
