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

from numpy import dot, zeros
from numpy.linalg import norm

from topic_modeling.visualize.models import Dataset, WordType
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetricValue
from django.db.models.aggregates import Count

metric_name = "Word Correlation"

@transaction.commit_manually
def add_metric(dataset, analysis):
    dataset = Dataset.objects.get(name=dataset)
    analysis = dataset.analyses.get(name=analysis)
    metric, created = analysis.pairwisedocumentmetrics.get_or_create(name=metric_name, analysis=analysis)
    if not created:
        raise RuntimeError("%s is already in the database for this analysis" % metric_name)
   
    word_types = WordType.objects.filter(tokens__doc__dataset=dataset).all()
    type_idx = dict((word_type,i) for i,word_type in enumerate(word_types))
    documents = dataset.documents.all()

    docwordvectors = [document_word_vector(type_idx, doc) for doc in documents]
    vectornorms = [norm(vector) for vector in docwordvectors]
    
    for i, doc1 in enumerate(documents):
        write('.')
        doc1_word_vals = docwordvectors[i]
        doc1_norm = vectornorms[i]
        for j, doc2 in enumerate(documents):
            doc2_word_vals = docwordvectors[j]
            doc2_norm = vectornorms[j]
            correlation_coeff = pmcc(doc1_word_vals, doc2_word_vals, doc1_norm,
                    doc2_norm)
            if not isnan(correlation_coeff):
                PairwiseDocumentMetricValue.objects.create(
                    document1=doc1, document2=doc2, metric=metric, value=correlation_coeff)
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


def document_word_vector(type_idx, document):
    document_word_vals = zeros(len(type_idx))
    for doc_wordtype_count in document.tokens.values('type__type').annotate(count=Count('type__type')):
        document_word_vals[type_idx[doc_wordtype_count['type__type']]] = doc_wordtype_count['count']
#    for i, word_type in enumerate(word_types):
#        document_word_vals[i] = document.tokens.filter(type=word_type).count()
        
    return document_word_vals
