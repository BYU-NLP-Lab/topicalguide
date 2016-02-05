from __future__ import division, print_function, unicode_literals
from collections import OrderedDict
from visualize.models import AnalysisMetricValue
import entropy
import token_count
import type_count
import stopword_count
import excluded_word_count

database_table = AnalysisMetricValue
metrics = OrderedDict([
    ('entropy', entropy),
    ('token_count', token_count),
    ('type_count', type_count),
    ('stopword_count', stopword_count),
    ('excluded_word_count', excluded_word_count),
])

def metric_exists(database_id, dataset_db, analysis_db, metric_db):
    return AnalysisMetricValue.objects.using(database_id).filter(analysis=analysis_db, metric=metric_db).exists()
