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

# from django.db import transaction
from math import log

from topic_modeling.visualize.models import Analysis, Dataset, DocumentMetric
from topic_modeling.visualize.models import DocumentMetricValue
from django.db.models.aggregates import Count

metric_name = 'Topic Entropy'
# @transaction.commit_manually
def add_metric(database_id, dataset, analysis):
    dataset = Dataset.objects.using(database_id).get(name=dataset)
    analysis = Analysis.objects.using(database_id).get(dataset=dataset, name=analysis)
    metric, created = DocumentMetric.objects.using(database_id).get_or_create(name=metric_name, analysis=analysis)
    if not created:
        raise RuntimeError('%s is already in the database for this analysis!' % metric_name)

    topics = analysis.topics.all()
    topic_ids = [topic.id for topic in topics]
    for document in dataset.documents.all():
        doc_token_count = document.tokens.count()
        entropy = 0
        if doc_token_count > 0:
            for count_obj in document.tokens.values('topics__id').annotate(count=Count('topics__id')):
                topic_id = count_obj['topics__id']
                if topic_id is not None and topic_id in topic_ids:
                    doctopic_count = count_obj['count']
                    if doctopic_count > 0:
                        prob = doctopic_count / doc_token_count
                        entropy -= prob * (log(prob) / log(2))
                        #TODO Decide if we care about this entropy being in bits (log base of 2)
        DocumentMetricValue.objects.using(database_id).create(document=document, metric=metric, value=entropy)
    # transaction.commit()

def metric_names_generated(dataset, analysis):
    return [metric_name]
