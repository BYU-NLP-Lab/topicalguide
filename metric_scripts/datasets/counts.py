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

from topic_modeling.visualize.models import DatasetMetric, DatasetMetricValue

def add_metric(dataset):
    token_metric, _ = DatasetMetric.objects.get_or_create(name="Token Count")
    type_metric, _ = DatasetMetric.objects.get_or_create(name="Type Count")
    
    token_count = 0
    type_count = 0
    for doc in dataset.document_set.all():
        token_count += doc.word_count
        type_count += doc.words.count()
    
    DatasetMetricValue.objects.create(metric=token_metric, dataset=dataset, value=token_count)
    DatasetMetricValue.objects.create(metric=type_metric, dataset=dataset, value=type_count)

def metric_names_generated(_dataset):
    return ["Token Count", "Type Count"]