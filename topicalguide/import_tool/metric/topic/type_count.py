from __future__ import division, print_function, unicode_literals
from django.db.models import Count


metric_name = 'Type Count'

def compute_metric(database_id, dataset_db, analysis_db):
    topic_word_type_query = analysis_db.tokens.values('topics').distinct().annotate(count=Count('word_type', distinct=True))
    results = []
    for row in topic_word_type_query:
        results.append({
            'topic_id': row['topics'],
            'value': row['count'],
        })
    return results
