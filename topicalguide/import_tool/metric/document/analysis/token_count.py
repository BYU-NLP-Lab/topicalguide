from __future__ import division, print_function, unicode_literals
from django.db.models import Count


metric_name = 'Token Count'

def compute_metric(database_id, dataset_db, analysis_db):
    query = analysis_db.tokens.values('document').annotate(count=Count('document'))
    
    results = []
    for result in query:
        results.append({
            'document_id': result['document'], 
            'analysis': analysis_db, 
            'value': result['count'], 
        })
    return results
