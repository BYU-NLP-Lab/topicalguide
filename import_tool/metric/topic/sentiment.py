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



import os, sys

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

# from django.db import transaction
from math import log
from optparse import OptionParser
from subprocess import Popen, PIPE

from topic_modeling.visualize.models import Analysis, TopicMetric
from topic_modeling.visualize.models import TopicMetricValue

# @transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    try:
        metric = TopicMetric.objects.get(name='Percent Tokens Positive '
                'Sentiment', analysis=analysis)
        if not force_import:
            raise RuntimeError('Sentiment is already in the database '
                    'for this analysis!')
    except TopicMetric.DoesNotExist:
        metric = TopicMetric(name='Percent Tokens Positive Sentiment',
                analysis=analysis)
        metric.save()

    # call stuff to classify documents and get sentiment information, as in
    # parse_dependencies.py

    data_root = analysis.dataset.dataset_dir
    topics = analysis.topics.all()
    for topic in topics:
        positive = 0;
        negative = 0;
        for docTopic in topic.documenttopic_set.all():
            filename = data_root + '/' + docTopic.document.filename
            print topic, filename
            sentiment = float(sentiment_document(filename))
            print 'sentiment returned:', sentiment
            if sentiment == 1 :
                positive += docTopic.count
            print '%d/%d' % (positive, topic.total_count)
        # compute aggregate information for topic
        topicSentiment = float(positive)/float(topic.total_count)
        tmv = TopicMetricValue(topic=topic, metric=metric, value=topicSentiment)
        tmv.save()
    # transaction.commit()


def sentiment_document(filename):
    # This is just temporary, so this line should be fixed once clean code is
    # committed
    cwd = '/aml/home/mjg82/tmp/sentiment/'
    args = ['java', '-mx1000m']
    args.append('SentimentDriver')
    base_command = ' '.join(args)
    command = base_command + ' ' + filename
    sentimentClassifier = Popen(command, stdout=PIPE, stderr=PIPE, cwd=cwd,
            shell=True)
    response = sentimentClassifier.communicate()[0]
    return response


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
    options, args = parser.parse_args()
    dataset = options.dataset_name
    analysis = options.analysis_name
    force_import = options.force_import
    add_metric(dataset, analysis, force_import)


# vim: et sw=4 sts=4
