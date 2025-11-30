from django.db.models import Count
from math import log


metric_name = 'Word Entropy'

def compute_metric(database_id, dataset_db, analysis_db):
    topic_counts_query = analysis_db.tokens.values('topics').annotate(count=Count('topics')).order_by('topics')
    topic_word_type_counts_query = analysis_db.tokens.values('topics', 'word_type').annotate(count=Count('word_type')).order_by('topics')
    topic_wt_iterator = iter(topic_word_type_counts_query)
    next_topic_wt_row = next(topic_wt_iterator)

    results = []
    for row in topic_counts_query:
        topic_id = row['topics']
        # Skip tokens with no topic assignment (outliers)
        if topic_id is None:
            continue
        topic_token_count = row['count']
        entropy = 0
        total_count_q = 0
        if topic_token_count > 0:
            while next_topic_wt_row['topics'] == topic_id:
                wt_count = next_topic_wt_row['count']
                if wt_count > 0:
                    prob = wt_count / topic_token_count
                    if prob > 0:  # Skip zero probabilities
                        entropy -= prob * log(prob, 2)
                try:
                    next_topic_wt_row = next(topic_wt_iterator)
                except:
                    break
            results.append({
                'topic_id': topic_id,
                'value': entropy,
            })
    return results
