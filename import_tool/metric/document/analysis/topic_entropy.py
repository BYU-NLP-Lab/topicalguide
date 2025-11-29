from django.db.models import Count
from math import log


metric_name = 'Topic Entropy'

def compute_metric(database_id, dataset_db, analysis_db):
    tokens_db = analysis_db.tokens
    doc_counts = tokens_db.values('document').annotate(count=Count('document')).order_by('document')
    doc_topic_counts_iter = iter(tokens_db.values('document', 'topics').annotate(count=Count('topics')).order_by('document'))
    next_doc_topic_row = next(doc_topic_counts_iter)

    for row in doc_counts:
        doc_token_count = row['count']
        doc_id = row['document']
        entropy = 0
        if doc_token_count > 0:
            while next_doc_topic_row['document'] == doc_id:
                doc_topic_count = next_doc_topic_row['count']
                if doc_topic_count > 0:
                    prob = doc_topic_count / doc_token_count
                    entropy -= prob * log(prob, 2)
                try:
                    next_doc_topic_row = next(doc_topic_counts_iter)
                except:
                    break
            yield {
                'document_id': doc_id,
                'analysis': analysis_db,
                'value': entropy,
            }
