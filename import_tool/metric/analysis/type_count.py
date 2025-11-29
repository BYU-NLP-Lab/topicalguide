from visualize.models import WordType


metric_name = 'Type Count'

def compute_metric(database_id, dataset_db, analysis_db):
    type_count = WordType.objects.using(database_id).filter(tokens__analysis=analysis_db).distinct().count()
    return [{'analysis': analysis_db, 'value': type_count }]
