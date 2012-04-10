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

from django.db import transaction

#from datetime import datetime
from numpy import dot, zeros
from numpy.linalg import norm

from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetricValue

metric_name = "Word Correlation"

@transaction.commit_manually
def add_metric(dataset, analysis):
    dataset = Dataset.objects.get(name=dataset)
    analysis = dataset.analysis_set.get(name=analysis)
    try:
        metric = analysis.pairwisedocumentmetric_set.get(name=metric_name)
        raise RuntimeError("%s is already in the database for this analysis" % metric_name)
    except PairwiseDocumentMetric.DoesNotExist:
        metric = PairwiseDocumentMetric(name=metric_name, analysis=analysis)
        metric.save()
    
    words = dataset.word_set
    num_words = words.count()

    documents = list(dataset.document_set.all())
    
    i = 0
    wordidx = {}
    for word in words.all():
        wordidx[word.id] = i
        i += 1
    
    docwordvectors = [document_word_vector(doc, num_words, wordidx) for doc in documents]
    vectornorms = [norm(vector) for vector in docwordvectors]
    
#    start = datetime.now()
    for i, doc1 in enumerate(documents):
        write('.')
#        print >> sys.stderr, 'Working on document', i, 'out of', num_docs
#        print >> sys.stderr, 'Time for last document:', datetime.now() - start
#        start = datetime.now()
        doc1_word_vals = docwordvectors[i]
        doc1_norm = vectornorms[i]
        for j, doc2 in enumerate(documents):
            doc2_word_vals = docwordvectors[j]
            doc2_norm = vectornorms[j]
            correlation_coeff = pmcc(doc1_word_vals, doc2_word_vals, doc1_norm,
                    doc2_norm)
            if not isnan(correlation_coeff):
                mv = PairwiseDocumentMetricValue(document1=doc1, 
                    document2=doc2, metric=metric, value=correlation_coeff)
                mv.save()
            else:
                pass
        transaction.commit()
    write('\n')

def write(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def metric_names_generated(_dataset, _analysis):
    return [metric_name]


def pmcc(doc1_topic_vals, doc2_topic_vals, doc1_norm, doc2_norm):
    return float(dot(doc1_topic_vals, doc2_topic_vals) /
            (doc1_norm * doc2_norm))


def document_word_vector(document, word_count, wordidx):
    document_word_vals = zeros(word_count)
    for docword in document.documentword_set.all():
        document_word_vals[wordidx[docword.word_id]] = docword.count
    return document_word_vals

# vim: et sw=4 sts=4
