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
        return "Top" + str(self.n)
    
    def name_topics(self, database_id, analysis_db):
        analysis_db.topics.prefetch_related('tokens')
        topic_names = {}
        for topic_db in analysis_db.topics.all():
            name = self._name_topic(topic_db)
            topic_names[topic_db.number] = name
        return topic_names

    def _name_topic(self,topic):
        top_n_items = topic.tokens.values("word_type__word")\
                      .annotate(count=Count("word_type__word"))\
                      .order_by('-count')[:self.n]
        return u' '.join(unicode(x['word_type__word']) for x in top_n_items)
