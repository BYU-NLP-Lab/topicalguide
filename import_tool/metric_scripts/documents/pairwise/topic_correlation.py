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

import sys

# from django.db import transaction

#from datetime import datetime
from numpy import dot, zeros
from numpy.linalg import norm

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetricValue

from topic_modeling.tools import TimeLongThing
import logging
logger = logging.getLogger('root')

metric_name = "Topic Correlation"

# @transaction.commit_manually
def add_metric(database_id, dataset, analysis):
    print 'begginning metric'
    sys.stdout.flush()
    logger.info('beginning metric: document > pairwise > topic correlation')
    try:
        dataset = Dataset.objects.using(database_id).get(name=dataset)
        analysis = Analysis.objects.using(database_id).get(dataset=dataset, name=analysis)
        metric,created = PairwiseDocumentMetric.objects.using(database_id).get_or_create(name=metric_name, analysis=analysis)
        if not created and PairwiseDocumentMetricValue.objects.using(database_id).filter(metric=metric).count():
            raise RuntimeError("%s is already in the database for this"
                    " analysis" % metric_name)
        
        topics = analysis.topics.all()
        topic_idx = {}
        for i, topic in enumerate(topics):
            topic_idx[topic] = i
        
        documents = list(dataset.documents.all())
        logger.info('Generating document topic vectors')
        print 'gen t vectors'
        sys.stdout.flush()
        num_docs = len(documents)

        timer = TimeLongThing(num_docs, 1, .05)
        doctopicvectors = []
        for doc in documents:
            timer.inc() 
            doctopicvectors.append(document_topic_vector(doc, topic_idx))

        vectornorms = [norm(vector) for vector in doctopicvectors]

        logger.info('Comparing the vectors')
        print 'compare vectors'
        sys.stdout.flush()
        timer = TimeLongThing(len(documents)**2, 5, 100)
        for i, doc1 in enumerate(documents):
    #        print >> sys.stderr, 'Working on document', i, 'out of', num_docs
    #        print >> sys.stderr, 'Time for last document:', datetime.now() - start
    #        start = datetime.now()
            logger.info('Working on document %d out of %d' % (i, num_docs))
            doc1_topic_vals = doctopicvectors[i]
            doc1_norm = vectornorms[i]
            for j, doc2 in enumerate(documents):
                timer.inc()
                sys.stderr.flush()
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
            # transaction.commit()
        write('\n')
    except:
        # transaction.rollback()
        raise

def metric_names_generated(_dataset, _analysis):
    return [metric_name]

def write(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def pmcc(doc1_topic_vals, doc2_topic_vals, doc1_norm, doc2_norm):
    return float(dot(doc1_topic_vals, doc2_topic_vals) /
            (doc1_norm * doc2_norm))


def document_topic_vector(document, topic_idx):
    document_topic_vals = zeros(len(topic_idx))
    for topic in topic_idx:
        doctopic_count = document.tokens.filter(topics=topic).count()
        document_topic_vals[topic_idx[topic]] = doctopic_count
#    for doctopic in document.documenttopic_set.all():
#        if doctopic.topic_id not in topic_idx:
#            continue
#        document_topic_vals[topic_idx[doctopic.topic_id]] = doctopic.count
    return document_topic_vals

# vim: et sw=4 sts=4
