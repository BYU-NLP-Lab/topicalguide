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

from topic_modeling.visualize.common.views import DatasetBaseView
from topic_modeling.visualize.models import Dataset, Analysis
import sys
from topic_modeling import anyjson
from django.http import HttpResponse

class TreemapView(DatasetBaseView):
    template_name = "treemaps.html"
    def __init__(self):
        return
    
    def get_context_data(self, request, **kwargs):
        analysis = Analysis.objects.all()
        context = super(TreemapView, self).get_context_data(request, **kwargs)
        context['datasets'] = []
        for i in range(len(analysis)):
            ana = analysis[i]
            if i == 0:
                context['default_dataset'] = {"title":ana.dataset.readable_name, "dataset_name":ana.dataset.name}
            context['datasets'].append({"title":ana.dataset.readable_name, "dataset_name":ana.dataset.name})      
        return context    

    

