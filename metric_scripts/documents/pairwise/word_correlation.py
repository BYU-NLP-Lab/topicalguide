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

from math import log
from numpy import dot, zeros
from numpy.linalg import norm
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, Dataset, Word
from topic_modeling.visualize.models import DocumentTopic
from topic_modeling.visualize.models import PairwiseDocumentMetric
from topic_modeling.visualize.models import PairwiseDocumentMetricValue

metric_name = "Word Correlation"
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
    
    num_words = Word.objects.order_by('-pk')[0].id + 1
    documents = list(dataset.document_set.all())

    docwordvectors = []
    for document in documents:
        docwordvectors.append(document_word_vector(document, num_words))
    
    for i, doc1 in enumerate(documents):
        doc1_word_vals = docwordvectors[i]
        for j, doc2 in enumerate(documents):
            doc2_word_vals = docwordvectors[j]
            correlation_coeff = pmcc(doc1_word_vals, doc2_word_vals)
            PairwiseDocumentMetricValue.objects.create(document1=doc1, 
                    document2=doc2, metric=metric, value=correlation_coeff)
    transaction.commit()
    

def metric_names_generated(dataset, analysis):
    return metric_name

def pmcc(doc1_word_vals, doc2_word_vals):
    return float(dot(doc1_word_vals, doc2_word_vals) / (norm(doc1_word_vals)
        * norm(doc2_word_vals)))


def document_word_vector(document, num_words):
    document_word_vals = zeros(num_words)
    for docword in document.documentword_set.all():
        document_word_vals[docword.word_id] = docword.count
    return document_word_vals


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
