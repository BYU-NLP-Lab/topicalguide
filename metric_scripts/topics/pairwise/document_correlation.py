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

from math import isnan
from math import log
from numpy import dot, zeros
from numpy.linalg import norm
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, Document
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetricValue

metric_name = "Document Correlation"
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

    num_docs = Document.objects.filter(dataset=analysis.dataset).order_by(
            '-pk')[0].id + 1
    topics = list(analysis.topic_set.all().order_by('number'))

    doctopicvectors = []
    for topic in topics:
        doctopicvectors.append(document_topic_vector(topic, num_docs))

    for i, topic1 in enumerate(topics):
        topic1_doc_vals = doctopicvectors[i]
        for j, topic2 in enumerate(topics):
            topic2_doc_vals = doctopicvectors[j]
            correlation_coeff = pmcc(topic1_doc_vals, topic2_doc_vals)
            if not isnan(correlation_coeff):
                PairwiseTopicMetricValue.objects.create(topic1=topic1,
                    topic2=topic2, metric=metric, value=correlation_coeff)
            else:
                print "Error computing metric between {0} and {1}".format(
                        topic1,topic2)
        transaction.commit()


def metric_names_generated(dataset, analysis):
    return [metric_name]


def pmcc(topic1_doc_vals, topic2_doc_vals):
    return float(dot(topic1_doc_vals, topic2_doc_vals) / (norm(topic1_doc_vals)
        * norm(topic2_doc_vals)))


def document_topic_vector(topic, num_docs):
    document_topic_vals = zeros(num_docs)
    for doctopic in topic.documenttopic_set.all():
        document_topic_vals[doctopic.document_id] = doctopic.count
    return document_topic_vals


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
