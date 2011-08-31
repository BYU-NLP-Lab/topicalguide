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

import os, sys

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from django.db import transaction

import sqlite3

from math import log
from numpy import dot, zeros
from numpy.linalg import norm
from optparse import OptionParser

from metric_scripts.topics.coherence import compute_pmi
from topic_modeling.visualize.models import Analysis, Word, TopicWord
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetricValue

metric_name = "Pairwise Coherence"
@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    try:
        metric = PairwiseTopicMetric.objects.get(name=metric_name,
                analysis=analysis)
        if not force_import:
            raise RuntimeError("%s is already in the database for this"
                    " analysis" % metric_name)
    except PairwiseTopicMetric.DoesNotExist:
        metric = PairwiseTopicMetric(name=metric_name, analysis=analysis)
        metric.save()

    conn = sqlite3.connect(kwargs['counts'])
    c = conn.cursor()
    c.execute('PRAGMA temp_store=MEMORY')
    c.execute('PRAGMA synchronous=OFF')
    c.execute('PRAGMA cache_size=2000000')
    c.execute('PRAGMA journal_mode=OFF')
    c.execute('PRAGMA locking_mode=EXCLUSIVE')
    c.execute("select words from total_counts")
    for row in c:
        total_words = float(row[0])
    c.execute("select cooccurrences from total_counts")
    for row in c:
        total_cooccurrences = float(row[0])

    topics = list(analysis.topic_set.all().order_by('number'))

    num_words = 10
    topicwords = []
    wordset = set()
    for topic in topics:
        words = topic_words(topic, num_words)
        topicwords.append(words)
        for w in words:
            wordset.add(w)

    for i, topic1 in enumerate(topics):
        print topic1
        topic1_words = topicwords[i]
        for j, topic2 in enumerate(topics):
            print ' ', topic2
            topic2_words = topicwords[j]
            coherence = pairwise_coherence(topic1_words, topic2_words, c,
                    total_words, total_cooccurrences)
            PairwiseTopicMetricValue.objects.create(topic1=topic1,
                    topic2=topic2, metric=metric, value=coherence)
    transaction.commit()


def pairwise_coherence(words1, words2, c, total_words, total_cooccurrences):
    total_pmi = 0
    for w1 in words1:
        for w2 in words2:
            total_pmi += compute_pmi(w1, w2, c, total_words,
                    total_cooccurrences)
    return total_pmi / len(words1) / len(words2)


def metric_names_generated(dataset, analysis):
    return [metric_name]


def topic_words(topic, num_words):
    return list([tw.word.type for tw in
        topic.topicword_set.order_by('-count')[:10]])


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
    parser.add_option('-f', '--force-import',
            dest='force_import',
            action='store_true',
            help='Force the import of this metric even if the script thinks the'
            ' metric is already in the database',
            )
    parser.add_option('-c', '--counts',
            dest='counts',
            help='Path to the database containing counts for computing PMI',
            )
    options, args = parser.parse_args()
    dataset = options.dataset_name
    analysis = options.analysis_name
    force_import = options.force_import
    counts = options.counts
    add_metric(dataset, analysis, force_import, counts=counts)

# vim: et sw=4 sts=4
