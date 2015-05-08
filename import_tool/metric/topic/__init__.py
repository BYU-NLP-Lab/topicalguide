from __future__ import division, print_function, unicode_literals
from collections import OrderedDict
from visualize.models import TopicMetricValue
#~ import alpha
#~ import attribute_entropy
#~ import coherence
#~ import sentiment
#~ import subset_document_entropy
#~ import subset_token_count
import token_count
import type_count
import document_entropy
import word_entropy
import temperature


database_table = TopicMetricValue
metrics = OrderedDict([
    #~ ('alpha', alpha), 
    #~ ('attribute_entropy', attribute_entropy), 
    #~ ('coherence', coherence), 
    #~ ('sentiment', sentiment), 
    #~ ('subset_document_entropy', subset_document_entropy), 
    #~ ('subset_token_count', subset_token_count), 
    ('token_count', token_count), 
    ('type_count', type_count), 
    ('document_entropy', document_entropy), 
    ('word_entropy', word_entropy), 
    ('temperature', temperature), 
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return TopicMetricValue.objects.using(database_id).filter(topic__analysis=analysis_db, metric=metric_db).exists()
