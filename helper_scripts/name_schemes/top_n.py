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

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import TopicNameScheme,TopicName,Topic,TopicWord

class TopNTopicNamer:
    def __init__(self,dataset_name,analysis_name,n):
        self.dataset_name = dataset_name
        self.analysis_name = analysis_name
        self.n = n
        
    def init(self):
        dataset = Dataset.objects.get(name=self.dataset_name)
        analysis = Analysis.objects.get(dataset=dataset, name=self.analysis_name)
        name_scheme,created = TopicNameScheme.objects.get_or_create(name=self.scheme_name(),analysis=analysis)
        return dataset,analysis,name_scheme,created
    
    def scheme_name(self):
        return "Top" + str(self.n)
    
    @transaction.commit_manually
    def name_all_topics(self):
        _,analysis,name_scheme,created = self.init()
        
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
        _,_,name_scheme,_ = self.init()
        name_scheme.delete()
        transaction.commit()
    
    def topic_name(self,topic):
        name = u""
        rankings = self.ranked_topic_terms(topic)
#        print rankings
        i = 0
        while i < self.n:
            name += rankings[i].word.type
            if i < self.n-1: name += u' '
            i += 1
        return name
    
    def ranked_topic_terms(self,topic):
        return  TopicWord.objects.filter(topic=topic).order_by('-count')

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-a', '--analysis-name',
        dest='analysis_name',
        help='The name of the analysis for which to add this topic metric',
    )
    parser.add_option('-n', '--top-n',
        dest='top_n',
        help='How many of the top terms by P(w|z) to include in the name',
        type='int'
    )
#    parser.add_option('-f', '--force-naming',
#            dest='force_naming',
#            action='store_true',
#            help='Force naming the topics in the analysis according to this name scheme'
#            ' even if ',
#            )
    
    options, args = parser.parse_args()
    namer = TopNTopicNamer(options.analysis_name,options.top_n)
    namer.name_all_topics()
    
# vim: et sw=4 sts=4
