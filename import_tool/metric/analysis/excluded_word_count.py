from __future__ import division, print_function, unicode_literals


metric_name = 'Excluded Word Count'

def compute_metric(database_id, dataset_db, analysis_db):
    count = analysis_db.excluded_words.count()
    return [{'analysis': analysis_db, 'value': count }]
