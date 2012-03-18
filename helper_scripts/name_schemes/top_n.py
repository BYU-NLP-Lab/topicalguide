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

from django.db.models.aggregates import Count

from django.db import transaction

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import TopicNameScheme,TopicName,Topic

class TopNTopicNamer:
    def __init__(self, dataset_name, analysis_name, n):
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

        i = 0
        # Protect against topics with small numbers of words
        while i < min(self.n, len(rankings)):
            name += rankings[i].type.type
            if i < self.n-1: name += u' '
            i += 1
        return name
    
    def ranked_topic_terms(self,topic):
        return topic.tokens.annotate(count=Count('id')).order_by('-count')

    
# vim: et sw=4 sts=4
