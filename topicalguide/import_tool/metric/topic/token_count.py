from __future__ import division, print_function, unicode_literals
from django.db.models import Count


metric_name='Token Count'

def compute_metric(database_id, dataset_db, analysis_db):
    topic_token_counts_query = analysis_db.tokens.values('topics').annotate(count=Count('topics'))
    results = []
    for row in topic_token_counts_query:
        results.append({
            'topic_id': row['topics'],
            'value': row['count'],
        })
    return results
