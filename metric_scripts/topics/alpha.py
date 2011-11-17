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

import os, sys

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from django.db import transaction
from math import log
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, TopicMetric
from topic_modeling.visualize.models import TopicMetricValue

metric_name = 'Alpha'
@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)

    try:
        metric = TopicMetric.objects.get(name=metric_name, analysis=analysis)
        if not force_import:
            raise RuntimeError('%s is already in the database for this '
                    'analysis!' % metric_name)
    except TopicMetric.DoesNotExist:
        metric = TopicMetric(name=metric_name, analysis=analysis)
        metric.save()
    if 'state_file' not in kwargs:
        raise RuntimeError('I need a state file for this metric!')
    state_file = open(kwargs['state_file'])
    # this is specific to mallet state files!
    _ = state_file.readline()
    alpha_vector = state_file.readline()
    alphas = alpha_vector.split(': ')[1].split()
    for number, alpha in enumerate(alphas):
        topic = analysis.topic_set.get(number=number)
        tmv = TopicMetricValue(topic=topic, metric=metric,
                value=float(alpha))
        tmv.save()
    transaction.commit()


def metric_names_generated(dataset, analysis):
    return [metric_name]


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-d', '--dataset-name',
            dest='dataset_name',
            help='The name of the dataset for which to add this topic metric',
            )
    parser.add_option('-a', '--analysis-name',
            dest='analysis_name',
            help='The name of the analysis for which to add this topic metric',
            )
    parser.add_option('-s', '--state-file',
            dest='state_file',
            help='The state file from which I can find the alpha values',
            )
    parser.add_option('-f', '--force-import',
            dest='force_import',
            action='store_true',
            help='Force the import of this metric even if the script thinks the'
            ' metric is already in the database',
            )
    options, args = parser.parse_args()
    dataset = options.dataset_name
    analysis = options.analysis_name
    force_import = options.force_import
    state_file = options.state_file
    add_metric(dataset, analysis, force_import, state_file=state_file)

# vim: et sw=4 sts=4
