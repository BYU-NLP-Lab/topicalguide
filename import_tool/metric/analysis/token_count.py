

metric_name = 'Token Count'

def compute_metric(database_id, dataset_db, analysis_db):
    token_count = analysis_db.tokens.count()
    return [{'analysis': analysis_db, 'value': token_count }]
