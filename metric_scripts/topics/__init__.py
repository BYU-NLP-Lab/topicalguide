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


from metric_scripts import MetricSet

import alpha
import attribute_entropy
import coherence
import document_entropy
import sentiment
import subset_document_entropy
import subset_token_count
import token_count
import type_count
import word_entropy

metrics = MetricSet()
metrics['alpha'] = alpha
metrics['attribute entropy'] = attribute_entropy
metrics['coherence'] = coherence
metrics['document entropy'] = document_entropy
metrics['sentiment'] = sentiment
metrics['subset document entropy'] = subset_document_entropy
metrics['subset token count'] = subset_token_count
metrics['token count'] = token_count
metrics['type count'] = type_count
metrics['word entropy'] = word_entropy

from pairwise import document_correlation
from pairwise import pairwise_coherence
from pairwise import word_correlation

pairwise_metrics = MetricSet()
pairwise_metrics['document correlation'] = document_correlation
pairwise_metrics['pairwise coherence'] = pairwise_coherence
pairwise_metrics['word correlation'] = word_correlation

# vim: et sw=4 sts=4
