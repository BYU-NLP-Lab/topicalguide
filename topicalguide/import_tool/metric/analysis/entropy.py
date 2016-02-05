from __future__ import division, print_function, unicode_literals
from django.db.models import Count
from math import log


metric_name = 'Entropy'

def compute_metric(database_id, dataset_db, analysis_db):
    # Get token counts for each topic.
    topic_token_counts_query = analysis_db.tokens.values('topics').annotate(count=Count('topics'))
    total = float(analysis_db.tokens.count())
    
    # Get probabilities.
    entropy = 0.0
    for row in topic_token_counts_query:
        prob = float(row['count']) / total
        entropy -= prob * log(prob, 2)
    return [{'analysis': analysis_db, 'value': entropy }]
