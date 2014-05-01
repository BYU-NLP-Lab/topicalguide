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
from collections import OrderedDict

from dataset import metrics as dataset_metrics
from document import metrics as document_metrics
from analysis import metrics as analysis_metrics
from topic import metrics as topic_metrics
from document.pairwise import metrics as document_pairwise_metrics
from topic.pairwise import metrics as topic_pairwise_metrics

all_metrics = OrderedDict()
name_extensions = OrderedDict([
    ('dataset_', dataset_metrics),
    ('document_', document_metrics),
    ('analysis_', analysis_metrics),
    ('topic_', topic_metrics),
    ('document_pairwise_', document_pairwise_metrics),
    ('topic_pairwise_', topic_pairwise_metrics),
])
for extension in name_extensions:
    for name in name_extensions[extension]:
        all_metrics[extension + name] = name_extensions[extension][name]
