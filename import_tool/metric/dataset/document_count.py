from __future__ import division, print_function, unicode_literals


metric_name = 'Document Count'

def compute_metric(database_id, dataset_db, analysis_db):
    document_count = dataset_db.documents.count()
    return [{'dataset': dataset_db, 'value': document_count }]
