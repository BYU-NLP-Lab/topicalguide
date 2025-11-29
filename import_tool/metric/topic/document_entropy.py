from django.db.models import Count
from math import log


metric_name = 'Document Entropy'

def compute_metric(database_id, dataset_db, analysis_db):
    results = []
    tokens_db = analysis_db.tokens
    topic_counts = tokens_db.values('topics').annotate(count=Count('topics')).order_by('topics')
    topic_doc_counts_iter = iter(tokens_db.values('document', 'topics').annotate(count=Count('document')).order_by('topics'))
    next_topic_doc_row = next(topic_doc_counts_iter)

    for row in topic_counts:
        topic_token_count = row['count']
        topic_id = row['topics']
        entropy = 0
        total_token_count = 0
        if topic_token_count > 0:
            while next_topic_doc_row['topics'] == topic_id:
                doc_id = next_topic_doc_row['document']
                topic_doc_count = next_topic_doc_row['count']
                if topic_doc_count > 0:
                    total_token_count += topic_doc_count
                    prob = topic_doc_count / topic_token_count
                    entropy -= prob * log(prob, 2)
                try:
                    next_topic_doc_row = next(topic_doc_counts_iter)
                except:
                    break
            results.append({
                'topic_id': topic_id,
                'value': entropy,
            })
    return results
