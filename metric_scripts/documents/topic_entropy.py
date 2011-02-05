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
from optparse import OptionParser

from topic_modeling.visualize.models import Analysis, Dataset, DocumentMetric
from topic_modeling.visualize.models import DocumentMetricValue

metric_name = 'Topic Entropy'
@transaction.commit_manually
def add_metric(dataset, analysis, force_import=False, *args, **kwargs):
    dataset = Dataset.objects.get(name=dataset)
    analysis = Analysis.objects.get(dataset=dataset, name=analysis)
    try:
        metric = DocumentMetric.objects.get(name=metric_name, analysis=analysis)
        if not force_import:
            raise RuntimeError('%s is already in the database for this '
                    ' analysis!' % metric_name)
    except DocumentMetric.DoesNotExist:
        metric = DocumentMetric(name=metric_name, analysis=analysis)
        metric.save()
    documents = dataset.document_set.all()
    for document in documents:
        entropy = 0
        for dt in document.documenttopic_set.all():
            prob = dt.count / document.word_count
            entropy -= prob * (log(prob) / log(2))
        dmv = DocumentMetricValue(document=document, metric=metric,
                value=entropy)
        dmv.save()
    transaction.commit()

def metric_names_generated(dataset, analysis):
    return [metric_name]

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
