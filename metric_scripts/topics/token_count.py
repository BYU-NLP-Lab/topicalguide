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

from topic_modeling.visualize.models import Analysis, TopicMetric
from topic_modeling.visualize.models import TopicMetricValue

metric_name='Number of tokens'
#@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    try:
        metric = TopicMetric.objects.get(name=metric_name,
                analysis=analysis)
        if not force_import:
            raise RuntimeError('Number of tokens is already in the database '
                    'for this analysis!')
    except TopicMetric.DoesNotExist:
        metric = TopicMetric(name='Number of tokens', analysis=analysis)
        metric.save()
    topics = analysis.topics.all()
    for topic in topics:
        tmv = TopicMetricValue(topic=topic, metric=metric,
                value=topic.tokens.count())
        tmv.save()
    # transaction.commit()

def metric_names_generated(dataset, analysis):
    return [metric_name]

# vim: et sw=4 sts=4
