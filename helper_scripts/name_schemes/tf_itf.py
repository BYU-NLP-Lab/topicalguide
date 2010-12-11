#!/usr/bin/env python

# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.


from __future__ import division

from django.db import transaction
from optparse import OptionParser
from operator import itemgetter

from django.db.models import Sum

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import TopicNameScheme,TopicName,Topic,TopicWord
import math

class TfitfTopicNamer:
    analysis = None
    name_scheme = None
    n = None
    total_number_of_topics = None
    
    def __init__(self,dataset_name,analysis_name,n):
        dataset = Dataset.objects.get(name=dataset_name)
        self.analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)
        self.n = n
        self.name_scheme,self.created = TopicNameScheme.objects.get_or_create(name=self.scheme_name(),analysis=self.analysis)
        self.total_number_of_topics = Topic.objects.filter(analysis=self.analysis).count()
    
    @staticmethod
    def scheme_name():
        return 'TF-ITF_topN'
    
    @transaction.commit_manually
    def name_all_topics(self):
        if self.created:
            topics = Topic.objects.filter(analysis=self.analysis)
            for topic in topics:
                print "topic:", topic
                name = self.topic_name(topic)
                print name.encode('utf-8')
                TopicName.objects.create(topic=topic,name_scheme=self.name_scheme,name=name)
            transaction.commit()
        else:
            print "Name scheme {0} already exists for analysis {1}. Skipping.".format(self.name_scheme, self.analysis)
    
    @transaction.commit_manually
    def unname_all_topics(self):
        self.name_scheme.delete()
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
        
        topic_words = TopicWord.objects.filter(topic=topic)
        total_tokens_in_topic = topic_words.aggregate(total_tokens_in_topic=Sum('count'))['total_tokens_in_topic']
#        total_tokens_in_topic = topic_words.sum('count')
        
        for topic_word in topic_words:
            topic = topic_word.topic
            tf_itf = self.tf_itf(topic_word,total_tokens_in_topic)
            term_rankings[topic_word.word.type] = tf_itf
        
        return sorted(term_rankings.iteritems(),key=itemgetter(1),reverse=True)
    
    def tf_itf(self,topic_word,total_tokens_in_topic):
        return self.term_frequency(topic_word.word,topic_word.topic,total_tokens_in_topic) * self.inverse_topic_frequency(topic_word.word)
    
    def term_frequency(self,term,topic,total_tokens_in_topic):
        term_count_in_topic = TopicWord.objects.filter(word=term,topic=topic).count()
        return term_count_in_topic / total_tokens_in_topic
        
    def inverse_topic_frequency(self,term):
        topics_containing_term = TopicWord.objects.filter(word=term).count()
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
