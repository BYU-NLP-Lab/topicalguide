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

from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.template.context import Context
from django.views.generic.base import TemplateResponseMixin, View

from topic_modeling.visualize.models import Dataset, Analysis
from topic_modeling.visualize import favorites

'''
Like TemplateView, but better
'''
class RootView(TemplateResponseMixin, View):
    def get_context_data(self, request, **kwargs):
        context = Context()
        
        STATIC = '/site-media'
        context['SCRIPTS'] = '/scripts'
        context['STYLES'] = '/styles'
        context['IMAGES'] = STATIC + '/images'
        context['FONTS'] = STATIC + '/fonts'
        
        context['topical_guide_project_url'] = "http://nlp.cs.byu.edu/topicalguide"
        context['nlp_lab_url'] = "http://nlp.cs.byu.edu"
        context['nlp_lab_logo_url'] = context['IMAGES'] + "/byunlp-135px.png"
        context['nlp_lab_small_logo_url'] = context['IMAGES'] + "/byunlp-35px.png"
        
        # Favorites Stuff
        # Do what's necessary to keep the session from ever expiring (assuming the user checks in every 100 years or so
        if request.session.get_expiry_age() < 3153600000: # If the session is expiring sometime in the next 100 years,
            request.session.set_expiry(timedelta(365000)) # then reset the expiration to 1,000 years from now
        
        # Preload lists of favorites
        context['favorites'] = {
            'datasets': favorites.dataset_favorite_entries(request),
            'analyses': favorites.analysis_favorite_entries(request),
            'topics': favorites.favorite_topic_entries(request)
        }
        
        context['favids'] = {
            'datasets': [fav['fav'].dataset.id for fav in context['favorites']['datasets']],
            'analyses': [fav['fav'].analysis.id for fav in context['favorites']['analyses']],
            'topics':   [fav['fav'].topic.id for fav in context['favorites']['topics']]
        }

        
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

class DatasetBaseView(RootView):
    def get_context_data(self, request, **kwargs):
        context = super(DatasetBaseView, self).get_context_data(request, **kwargs)
        context['datasets'] = Dataset.objects.all()
        try:
            dataset = get_object_or_404(Dataset, name=kwargs['dataset'])
        except KeyError:
            dataset = context['datasets'][0]
        
        context['dataset'] = dataset
        context['dataset_url'] = "/datasets/%s" % (dataset)
        
        return context

class AnalysisBaseView(DatasetBaseView):
    def get_context_data(self, request, **kwargs):
        context = super(AnalysisBaseView, self).get_context_data(request, **kwargs)
        
        analysis = get_object_or_404(Analysis, name=kwargs['analysis'], dataset=context['dataset'])
        context['analysis'] = analysis
        context['analysis_url'] = "%s/analyses/%s" % (context['dataset_url'],
                analysis.name)
    
        context['attributes_url'] = context['analysis_url'] + "/attributes"
        context['documents_url'] = context['analysis_url'] + "/documents"
        context['plots_url'] = context['analysis_url'] + "/plots"
        context['topics_url'] = context['analysis_url'] + "/topics"
        context['words_url'] = context['analysis_url'] + "/words"
        
#        context['favorites']['topics'] = favorites.favorite_topic_entries(request, context['dataset'], analysis.name)
        
        return context