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


from django.db.models.aggregates import Count

from django.db import transaction

from topic_modeling.visualize.models import Analysis, TopicNameScheme

class TopNTopicNamer:
    def __init__(self, dataset_name, analysis_name, n):
        self.dataset_name = dataset_name
        self.analysis_name = analysis_name
        self.n = n
    
    def scheme_name(self):
        return "Top" + str(self.n)
    
    @transaction.commit_manually
    def name_all_topics(self):
        analysis = Analysis.objects.get(dataset__name=self.dataset_name, name=self.analysis_name)
        name_scheme,created = analysis.topicnameschemes.get_or_create(name=self.scheme_name())
        
        if created:
            for i, topic in enumerate(analysis.topics.all()):
                name = self.topic_name(topic)
                print 'topic #%i: %s' % (i, name.encode('utf-8'))
                name_scheme.names.create(topic=topic, name=name)
            transaction.commit()
        else:
            print "Name scheme %s already exists for analysis %s. Skipping." % (name_scheme, analysis)
    
    @transaction.commit_manually
    def unname_all_topics(self):
        try:
            analysis = Analysis.objects.get(dataset__name=self.dataset_name, name=self.analysis_name)
            name_scheme = analysis.topicnameschemes.get(name=self.scheme_name())
            name_scheme.delete()
            transaction.commit()
        except TopicNameScheme.DoesNotExist:
            pass
    
    def topic_name(self,topic):
        top_n_items = topic.tokens.values("type__type")\
                      .annotate(count=Count("type__type"))\
                      .order_by('-count')[:self.n]
        return u' '.join(x['type__type'] for x in top_n_items)
