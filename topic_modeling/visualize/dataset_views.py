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

from random import randint
from topic_modeling.visualize.common.ui import BreadCrumb
from topic_modeling.visualize.common.views import DatasetBaseView


'''
    The image urls data structure:
    {dataset_obj: {
        'analysis_img_urls': {
            analysis_obj: '...'
            }
        },
        'initial_plot_img_url': '...'
    }
'''
class DatasetView(DatasetBaseView):
    template_name = "datasets.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(DatasetView, self).get_context_data(request, **kwargs)
        
        context['view_description'] = 'Available Datasets'
        context['breadcrumb'] = BreadCrumb().item('Available Datasets')
        
        
        img_urls = dict()
        
        # Randomly generate the parameters that will be used in generation of plots
        # We do this for every analysis so that each analysis has its own plot
        for dataset in context['datasets']:
            img_urls[dataset] = dict()
            analysis_img_urls = dict()
            attributes = dataset.attribute_set.all()
            
            if len(attributes) > 0 and dataset.analysis_set.count() > 0:
                for i, analysis in enumerate(dataset.analysis_set.all()):
                    
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
                    plot_img_url += '?fmt=png'
                    
                    analysis_img_urls[analysis] = plot_img_url
                    
                    if i == 0: img_urls[dataset]['initial_plot_img_url'] = plot_img_url
            else:
                img_urls[dataset]['initial_plot_img_url'] = None
            
            img_urls[dataset]['analysis_img_urls'] = analysis_img_urls
        context['plot_img_urls'] = img_urls
        return context

    def _sample_list(self, list):
        return list[randint(0, len(list) - 1)]
# vim: et sw=4 sts=4
