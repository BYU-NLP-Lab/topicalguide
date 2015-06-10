from __future__ import division, print_function, unicode_literals
from django.db import transaction
from django.db.models.aggregates import Count
from abstract_topic_namer import AbstractTopicNamer
from visualize.models import TopicNameScheme, TopicName


class TopNTopicNamer(AbstractTopicNamer):
    def __init__(self, n=3):
        self.n = n
    
    @property
    def name_scheme(self):
        return 'Top ' + str(self.n)
    
    def name_topics(self, database_id, analysis_db):
        analysis_db.topics.prefetch_related('tokens')
        topic_names = {}
        for topic_db in analysis_db.topics.all():
            name = self._name_topic(topic_db)
            topic_names[topic_db.number] = name
        return topic_names

    def _name_topic(self,topic):
        top_n_items_query = topic.tokens.values_list('word_type_abstraction')\
            .annotate(count=Count('word_type_abstraction'))\
            .order_by('-count')[:self.n]
        abstraction_to_index = {}
        index = 0
        for row in top_n_items_query:
            abstraction_to_index[row[0]] = index # ID of the word abstraction
            index += 1
        actual_words_query = topic.tokens.values_list('word_type__word', 'word_type_abstraction')\
            .annotate(count=Count('word_type__word'))\
            .filter(word_type_abstraction__in=[key for key in abstraction_to_index])
        top_n_words = [('__', 0) for _ in abstraction_to_index]
        for row in actual_words_query:
            index = abstraction_to_index[row[1]]
            word, count = top_n_words[index]
            if row[2] > count or (row[2] == count and len(row[0]) < len(word)):
                top_n_words[index] = (row[0], row[2])
        result = u', '.join([t[0] for t in top_n_words])
        return result
