#!/usr/bin/env python

# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.


from __future__ import division

from django.db import transaction
from optparse import OptionParser
from operator import itemgetter

from django.db.models import Sum

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import TopicNameScheme,TopicName,Topic
import math

class TfitfTopicNamer:
    def __init__(self,dataset_name,analysis_name,n):
        self.dataset_name = dataset_name
        self.analysis_name = analysis_name
        self.n = n
        
    def init(self):
        dataset = Dataset.objects.get(name=self.dataset_name)
        analysis = Analysis.objects.get(dataset=dataset, name=self.analysis_name)
        name_scheme,created = TopicNameScheme.objects.get_or_create(name=self.scheme_name(),analysis=analysis)
        total_number_of_topics = Topic.objects.filter(analysis=analysis).count()
        return dataset,analysis,name_scheme,created,total_number_of_topics
    
    def scheme_name(self):
        return 'TF-ITF_top' + str(self.n)
    
    @transaction.commit_manually
    def name_all_topics(self):
        _,analysis,name_scheme,created,self.total_number_of_topics = self.init()
        if created:
            topics = Topic.objects.filter(analysis=analysis)
            for topic in topics:
                print "topic:", topic
                name = self.topic_name(topic)
                print name.encode('utf-8')
                TopicName.objects.create(topic=topic,name_scheme=name_scheme,name=name)
            transaction.commit()
        else:
            print "Name scheme {0} already exists for analysis {1}. Skipping.".format(name_scheme, analysis)
    
    @transaction.commit_manually
    def unname_all_topics(self):
        _,_,name_scheme,_,_ = self.init()
        name_scheme.delete()
        transaction.commit()
    
    def topic_name(self,topic):
        name = u""
        rankings = self.ranked_topic_terms(topic)
#        print rankings
        i = 0
        while i < self.n:
            name += rankings[i][0]
            if i < self.n-1: name += u' '
            i += 1
        return name
    
    def ranked_topic_terms(self,topic):
        term_rankings = {}
        
        total_tokens_in_topic = topic.tokens.count()
#        topic_words = TopicWord.objects.filter(topic=topic)
#        total_tokens_in_topic = topic_words.aggregate(total_tokens_in_topic=Sum('count'))['total_tokens_in_topic']
#        total_tokens_in_topic = topic_words.sum('count')
        
        for topic_word in topic_words:
            topic = topic_word.topic
            tf_itf = self.tf_itf(topic_word,total_tokens_in_topic)
            term_rankings[topic_word.word.type] = tf_itf
        
        return sorted(term_rankings.iteritems(),key=itemgetter(1),reverse=True)
    
    def tf_itf(self,analysis, topic_word,total_tokens_in_topic):
        return self.term_frequency(topic_word.word,topic_word.topic,total_tokens_in_topic) * self.inverse_topic_frequency(analysis, topic_word.word)
    
    def term_frequency(self,term,topic,total_tokens_in_topic):
        term_count_in_topic = topic.tokens.filter(type__type=term).count()
#        term_count_in_topic = TopicWord.objects.filter(word=term,topic=topic).count()
        return term_count_in_topic / total_tokens_in_topic
        
    def inverse_topic_frequency(self, analysis, term):
        topics_containing_term = analysis.topics.filter(tokens__type__type=term).count()
#        topics_containing_term = TopicWord.objects.filter(word=term).count()
        return math.log(self.total_number_of_topics / topics_containing_term)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-a', '--analysis-name',
        dest='analysis_name',
        help='The name of the analysis for which to add this topic metric',
    )
    parser.add_option('-n', '--top-n',
        dest='top_n',
        help='How many of the top terms by TF-ITF to include in the name',
        type='int'
    )
#    parser.add_option('-f', '--force-naming',
#            dest='force_naming',
#            action='store_true',
#            help='Force naming the topics in the analysis according to this name scheme'
#            ' even if ',
#            )
    
    options, args = parser.parse_args()
    namer = TfitfTopicNamer(options.analysis_name,options.top_n)
    namer.name_all_topics()
    
# vim: et sw=4 sts=4
