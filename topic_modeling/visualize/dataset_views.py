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

from random import randint
from topic_modeling.visualize.common.ui import BreadCrumb
from topic_modeling.visualize.common.views import DatasetBaseView

class DatasetView(DatasetBaseView):
    template_name = "datasets.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(DatasetView, self).get_context_data(request, **kwargs)
        
        context['view_description'] = 'Available Datasets'
        context['breadcrumb'] = BreadCrumb().item('Available Datasets')
        
        # Randomly generate the parameters that will be used in generation of plots
        # We do this for every analysis so that each analysis has its own plot
        context['plot_img_urls'] = dict()
        
        for dataset in context['datasets']:
            context['plot_img_urls'][dataset] = dict()
            
            attributes = dataset.attribute_set.all()
            
            for analysis in dataset.analysis_set.all():
                if len(attributes) > 0:
                    attribute = self._sample_list(attributes)
                    attrvalues = attribute.attributevalue_set.all()
                    attrvalues = [attrval.value.id for attrval in attrvalues]
                
                    topics = analysis.topic_set.all()
                    topics = [self._sample_list(topics), self._sample_list(topics), self._sample_list(topics)]
                    topics = [topic.id for topic in topics]
                    
                    plot_img_url = "/feeds/topic-attribute-plot/"
                    plot_img_url += 'attributes/'+str(attribute.id)+'/'
                    plot_img_url += "values/" + '.'.join([str(x) for x in attrvalues])
                    plot_img_url += "/topics/"
                    plot_img_url += '.'.join([str(x) for x in topics])
                    
                    context['plot_img_urls'][dataset][analysis] = plot_img_url
        return context

    def _sample_list(self, list):
        return list[randint(0, len(list) - 1)]
# vim: et sw=4 sts=4
