from django.db.models import Count
from visualize.models import WordType
from math import isnan
from numpy import dot, zeros
from numpy.linalg import norm


metric_name = "Word Correlation"

def compute_metric(database_id, dataset_db, analysis_db):
    word_types_query = WordType.objects.using(database_id).filter(tokens__analysis=analysis_db).distinct()
    word_idx = {word_type.id: i for i, word_type in enumerate(word_types_query)}
    topic_word_type_query = analysis_db.tokens.values('topics__number', 'word_type').annotate(count=Count('word_type'))
    topics_idx = {topic.number: topic.id for topic in analysis_db.topics.all()}
    topic_count = len(topics_idx)
    word_type_count = len(word_idx)
    
    # Create topic by word type matrix that stores the intersecting counts
    topicwordvectors = [zeros(word_type_count) for i in range(0, topic_count)]
    for row in topic_word_type_query:
        topic_num = row['topics__number']
        # Skip tokens with no topic assignment (outliers)
        if topic_num is None:
            continue
        word_index = word_idx[row['word_type']]
        count = row['count']
        topicwordvectors[topic_num][word_index] = count
    
    for i in range(0, topic_count):
        for j in range(0, topic_count):
            topic1_word_vals = topicwordvectors[i]
            topic2_word_vals = topicwordvectors[j]
            topic1 = topics_idx[i]
            topic2 = topics_idx[j]
            if i == j:
                correlation_coeff = 1.0
            else:
                correlation_coeff = pmcc(topic1_word_vals, topic2_word_vals)
            if not isnan(correlation_coeff):
                yield {
                    'origin_topic_id': topic1,
                    'ending_topic_id': topic2,
                    'value': correlation_coeff, 
                }
            else:
                print("Error computing metric between topic {0} and topic {1}".format(topic1,topic2))

def pmcc(topic1_word_vals, topic2_word_vals):
    return float(dot(topic1_word_vals, topic2_word_vals) /
            (norm(topic1_word_vals) * norm(topic2_word_vals)))
