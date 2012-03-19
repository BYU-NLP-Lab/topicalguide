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

from math import isnan
from numpy import dot, zeros
from numpy.linalg import norm

from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import PairwiseTopicMetric
from topic_modeling.visualize.models import PairwiseTopicMetricValue

metric_name = "Document Correlation"
@transaction.commit_manually
def add_metric(dataset_name, analysis_name):
    dataset = Dataset.objects.get(name=dataset_name)
    analysis = dataset.analyses.get(name=analysis_name)
    
    metric, created = PairwiseTopicMetric.objects.get_or_create(name=metric_name,
                analysis=analysis)
    
    if created:
        raise RuntimeError("%s is already in the database for this analysis" % metric_name)

    docs = dataset.documents.all()
    next_idx = 0
    doc_idx = dict()
    for doc in docs:
        doc_idx[doc] = next_idx
        next_idx += 1
    
#    num_docs = dataset.documents.count()
#    num_docs = Document.objects.filter(dataset=analysis.dataset).order_by(
#            '-pk')[0].id + 1
    topics = analysis.topics.order_by('number').all()

    doctopicvectors = []
    for topic in topics:
        doctopicvectors.append(document_topic_vector(topic, doc_idx))

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

#t.tokens.filter(doc=d).count()
def document_topic_vector(topic, doc_idx):
    document_topic_vals = zeros(len(doc_idx))
    for i,doc in doc_idx.items():
        document_topic_vals[i] = topic.tokens.filter(doc=doc).count()
#    for doctopic in topic.documenttopic_set.all():
#        document_topic_vals[doctopic.document_id] = doctopic.count
    return document_topic_vals
