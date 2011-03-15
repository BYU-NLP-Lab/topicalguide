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

import os, sys, sqlite3

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from django.db import transaction
from math import log
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, TopicMetric
from topic_modeling.visualize.models import TopicMetricValue

metric_name = 'Coherence'
@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    try:
        metric = TopicMetric.objects.get(name=metric_name,
                analysis=analysis)
        if not force_import:
            raise RuntimeError('%s is already in the database for this '
                    'analysis!' % metric_name)
    except TopicMetric.DoesNotExist:
        metric = TopicMetric(name=metric_name, analysis=analysis)
        metric.save()

    conn = sqlite3.connect(kwargs['counts'])
    c = conn.cursor()
    c.execute("select words from total_counts")
    for row in c:
        total_words = float(row[0])
    c.execute("select cooccurrences from total_counts")
    for row in c:
        total_cooccurrences = float(row[0])
    topics = analysis.topic_set.all()
    for topic in topics:
        topicwords = topic.topicword_set.filter(
                word__ngram=False).order_by('-count')
        # We just grab the first ten words - there's probably a better way to
        # do this
        words = [tw.word.type for tw in topicwords[:10]]
        total_pmi = 0
        for w1 in words:
            for w2 in words:
                if w1 == w2: continue
                total_pmi += compute_pmi(w1, w2, c, total_words,
                        total_cooccurrences)
        average_pmi = total_pmi / (len(words)**2)
        tmv = TopicMetricValue(topic=topic, metric=metric, value=average_pmi)
        tmv.save()
    transaction.commit()


def metric_names_generated(dataset, analysis):
    return [metric_name]


def compute_pmi(word1, word2, c, total_words, total_cooccurrences, seen_w={},
        seen_c={}):
    # We memoize here, because we do a lot of lookups.
    pair = '%s,%s' % (word1, word2)
    if pair in seen_c:
        return seen_c[pair]
    w1_count = None
    w2_count = None
    cooccurrence_count = None
    if word2 < word1:
        word1, word2 = word2, word1
    if word1 in seen_w:
        w1_count = seen_w[word1]
    else:
        c.execute("select count from word_counts where word = '%s';" % word1)
        for row in c:
            w1_count = row[0]
        seen_w[word1] = w1_count
    if word2 in seen_w:
        w2_count = seen_w[word2]
    else:
        c.execute("select count from word_counts where word = '%s';" % word2)
        for row in c:
            w2_count = row[0]
        seen_w[word2] = w2_count
    c.execute("select count from cooccurrence_counts where word_pair = '%s';"
            % pair)
    for row in c:
        cooccurrence_count = row[0]
    if not cooccurrence_count or not w1_count or not w2_count:
        seen_c[pair] = 0
        return 0
    pmi = log(cooccurrence_count / total_cooccurrences * total_words *
            total_words / w1_count / w2_count)
    seen_c[pair] = pmi
    return pmi


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
    parser.add_option('-c', '--counts',
            dest='counts',
            help='Path to the database containing counts for computing PMI',
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
    counts = options.counts
    add_metric(dataset, analysis, force_import, counts=counts)

# vim: et sw=4 sts=4
