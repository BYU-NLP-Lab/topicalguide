from django.db.models import Count
from math import isnan
from numpy import dot, zeros
from numpy.linalg import norm


metric_name = 'Document Correlation'

def compute_metric(database_id, dataset_db, analysis_db):
    doc_idx = {doc.id: doc.index for doc in dataset_db.documents.all()}
    topics_idx = {topic.number: topic.id for topic in analysis_db.topics.all()}
    topic_count = len(topics_idx)
    topic_doc_word_type_counts = analysis_db.tokens.values('topics__number', 'document__index').annotate(count=Count('word_type')).order_by('topics__number')
    
    # Collect word type counts into a topic by document matrix
    doc_count = len(doc_idx)
    doctopicvectors = [zeros(doc_count) for i in range(0, topic_count)]
    for row in topic_doc_word_type_counts:
        topic_num = row['topics__number']
        doc_index = row['document__index']
        count = row['count']
        doctopicvectors[topic_num][doc_index] = count
    
    
    for i in range(0, topic_count):
        for j in range(0, topic_count):
            topic1_doc_vals = doctopicvectors[i]
            topic2_doc_vals = doctopicvectors[j]
            topic1 = topics_idx[i]
            topic2 = topics_idx[j]
            if i == j:
                correlation_coeff = 1.0
            else:
                correlation_coeff = pmcc(topic1_doc_vals, topic2_doc_vals)
            if not isnan(correlation_coeff):
                yield {
                    'origin_topic_id': topic1,
                    'ending_topic_id': topic2,
                    'value': correlation_coeff,
                }
            else:
                print("Error computing metric between topic {0} and topic {1}".format(topic1,topic2))

def pmcc(topic1_doc_vals, topic2_doc_vals):
    return float(dot(topic1_doc_vals, topic2_doc_vals) / (norm(topic1_doc_vals)
        * norm(topic2_doc_vals)))
