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
from math import isnan

import os, sys

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from django.db import transaction

from datetime import datetime
from numpy import dot, zeros
from numpy.linalg import norm
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetricValue

metric_name = "Topic Correlation"
@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    dataset = Dataset.objects.get(name=dataset)
    analysis = Analysis.objects.get(dataset=dataset, name=analysis)
    try:
        metric = PairwiseDocumentMetric.objects.get(name=metric_name,
                analysis=analysis)
        if not force_import:
            raise RuntimeError("%s is already in the database for this"
                    " analysis" % metric_name)
    except PairwiseDocumentMetric.DoesNotExist:
        metric = PairwiseDocumentMetric(name=metric_name, analysis=analysis)
        metric.save()
    
    topics = analysis.topic_set.all()
    topic_idx = {}
    for i, topic in enumerate(topics):
        topic_idx[topic.id] = i
    
    documents = list(dataset.document_set.all())
    doctopicvectors = [document_topic_vector(doc, topic_idx)
            for doc in documents]
    vectornorms = [norm(vector) for vector in doctopicvectors]
    num_docs = len(documents)
    
    start = datetime.now()
    for i, doc1 in enumerate(documents):
        sys.stdout.write('.')
#        print >> sys.stderr, 'Working on document', i, 'out of', num_docs
#        print >> sys.stderr, 'Time for last document:', datetime.now() - start
        start = datetime.now()
        doc1_topic_vals = doctopicvectors[i]
        doc1_norm = vectornorms[i]
        for j, doc2 in enumerate(documents):
            doc2_topic_vals = doctopicvectors[j]
            doc2_norm = vectornorms[j]
            correlation_coeff = pmcc(doc1_topic_vals, doc2_topic_vals,
                    doc1_norm, doc2_norm)
            if not isnan(correlation_coeff):
                mv = PairwiseDocumentMetricValue(document1=doc1, 
                    document2=doc2, metric=metric, value=correlation_coeff)
                mv.save()
            else:
                pass
        transaction.commit()
    sys.stdout.write('\n')

def metric_names_generated(dataset, analysis):
    return [metric_name]


def pmcc(doc1_topic_vals, doc2_topic_vals, doc1_norm, doc2_norm):
    return float(dot(doc1_topic_vals, doc2_topic_vals) /
            (doc1_norm * doc2_norm))


def document_topic_vector(document, topic_idx):
    document_topic_vals = zeros(len(topic_idx))
    for doctopic in document.documenttopic_set.all():
        if doctopic.topic_id not in topic_idx:
            continue
        document_topic_vals[topic_idx[doctopic.topic_id]] = doctopic.count
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
