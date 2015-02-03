from __future__ import division, print_function, unicode_literals
from visualize.models import WordType


metric_name = 'Type Count'

def compute_metric(database_id, dataset_db, analysis_db):
    query = analysis_db.tokens.values('document', 'word_type').distinct()
    doc_counts = {}
    for result in query:
        doc_counts[result['document']] = doc_counts.setdefault(result['document'], 0) + 1
    
    results = []
    for doc_id, count in doc_counts.iteritems():
        results.append({
            'document_id': doc_id, 
            'analysis': analysis_db, 
            'value': count, 
        })
    
    return results
