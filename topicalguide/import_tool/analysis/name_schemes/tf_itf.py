from __future__ import division, print_function, unicode_literals
from django.db import transaction
from django.db.models import Sum
from abstract_topic_namer import AbstractTopicNamer
from visualize.models import TopicNameScheme, TopicName
from django.db import transaction, connections
import math


# The TF-ITF score is computed as follows:
#   Let T be the number of topics, f(word_type, t) be the number of
#   occurances of word_type in the topic t, and c(word_type) be the 
#   count of the number of topics containing the word_type.
#   TF-ITF = f(word_type, t)*log(T/c(word_type))
class TfitfTopicNamer(AbstractTopicNamer):
    def __init__(self, n):
        self.n = n
    
    @property
    def name_scheme(self):
        return 'TF-ITF Top '+unicode(self.n)
    
    def name_topics(self, database_id, analysis_db):
        def compare_float(a, b):
            if a < b:
                return 1
            elif a > b:
                return -1
            else:
                return 0

        analysis_db.topics.prefetch_related('tokens')
        topic_count = analysis_db.topics.count()
        
        # Calculate ITF
        ITF = analysis_db.topic_word_type_occurrences()
        for key, value in ITF.iteritems():
            ITF[key] = math.log(topic_count)-math.log(value)
        
        topic_names = {}
        # Calculate TF-ITF scores and take the max
        for topic_db in analysis_db.topics.all():
            topic_tf_itf = topic_db.word_token_type_counts(words='*')
            for word, count in topic_tf_itf.iteritems():
                topic_tf_itf[word] = count*ITF[word]
            
            name = u' '.join([unicode(word) for word, count in \
                sorted([(key, value) for key, value in topic_tf_itf.iteritems()],
                        compare_float)[:self.n]])
            
            topic_names[topic_db.number] = name
        return topic_names
