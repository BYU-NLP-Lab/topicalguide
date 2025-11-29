from collections import OrderedDict
from visualize.models import AnalysisMetricValue
from . import entropy
from . import token_count
from . import type_count
from . import stopword_count
from . import excluded_word_count

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
