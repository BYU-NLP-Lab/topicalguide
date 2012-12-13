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

# from django.db import transaction

from topic_modeling.visualize.models import Analysis, TopicMetric
from topic_modeling.visualize.models import TopicMetricValue

metric_name = 'Alpha'
# @transaction.commit_manually
def add_metric(dataset, analysis, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    metric, created = TopicMetric.objects.get_or_create(name=metric_name, analysis=analysis)
    if not created:
        raise RuntimeError('%s is already in the database for this analysis!' % metric_name)
    
    if 'state_file' not in kwargs:
        raise RuntimeError('I need a state file for this metric!')
    state_file = open(kwargs['state_file'])
    # this is specific to mallet state files!
    _ = state_file.readline()
    alpha_vector = state_file.readline()
    alphas = alpha_vector.split(': ')[1].split()
    for number, alpha in enumerate(alphas):
        topic = analysis.topics.get(number=number)
        TopicMetricValue.objects.create(topic=topic, metric=metric, value=float(alpha))
    # transaction.commit()


def metric_names_generated(dataset, analysis):
    return [metric_name]
