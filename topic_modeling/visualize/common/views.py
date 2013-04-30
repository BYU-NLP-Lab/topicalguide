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

from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.template.context import Context
from django.views.generic.base import TemplateResponseMixin, View

from topic_modeling.visualize.models import Dataset, Analysis
from topic_modeling.visualize.favorites import dataset_favorite_entries, analysis_favorite_entries, favorite_topic_entries, \
    topic_view_favorite_entries, document_view_favorite_entries, favorite_document_entries

'''
Like TemplateView, but better
'''
class RootView(TemplateResponseMixin, View):
    def get_context_data(self, request, **kwargs):
        context = Context()

        STATIC = '/site-media'
        context['SCRIPTS'] = STATIC + '/scripts'
        context['STYLES'] = STATIC + '/styles'
        context['IMAGES'] = STATIC + '/images'
        context['FONTS'] = STATIC + '/fonts'
        context['license'] = "http://www.gnu.org/licenses/agpl.html"
        context['topical_guide_project_url'] = "http://nlp.cs.byu.edu/topicalguide"
        context['nlp_lab_url'] = "http://nlp.cs.byu.edu"
        context['nlp_lab_logo_url'] = context['IMAGES'] + "/byunlp-135px.png"
        context['nlp_lab_small_logo_url'] = context['IMAGES'] + "/byunlp-35px.png"
        context['in_iframe'] = 'in_iframe' in request.GET

        # Favorites Stuff
        # Do what's necessary to keep the session from ever expiring (assuming the user checks in every 10 years or so
        if request.session.get_expiry_age() < 315360000: # If the session is expiring sometime in the next 10 years,
            request.session.set_expiry(timedelta(3650)) # then reset the expiration to 10 years from now

        # Preload lists of favorites
        context['favorites'] = {
            'datasets': dataset_favorite_entries(request),
            'analyses': analysis_favorite_entries(request),
            'topics': favorite_topic_entries(request) + topic_view_favorite_entries(request),
            'documents': document_view_favorite_entries(request)
        }

        context['favids'] = {
            'datasets': [fav['fav'].dataset.id for fav in context['favorites']['datasets']],
            'analyses': [fav['fav'].analysis.id for fav in context['favorites']['analyses']],
            'topics':   [fav['fav'].topic.id for fav in context['favorites']['topics']],
            'documents':     [fav['fav'].document.id for fav in context['favorites']['documents']]
        }


        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, **kwargs)
        return self.render_to_response(context)

class TermsView(RootView):
    template_name = 'terms.html'

class DatasetBaseView(RootView):
    def get_context_data(self, request, **kwargs):
        context = super(DatasetBaseView, self).get_context_data(request, **kwargs)
	context['datasets'] = Dataset.objects.filter(visible=True)
        try:
            dataset = get_object_or_404(Dataset, name=kwargs['dataset'])
        except KeyError:
	    try:
		dataset = context['datasets'][0]
	    except IndexError:
		raise Exception('Misconfigured Database: you need to import a dataset first. Try running ./backend.py')

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
        # Set up entity-level document favorites. We do this in AnalysisBaseView because our document URLs still rely
        # on the name of the current analysis
        context['favorites']['documents'] = favorite_document_entries(request, kwargs['dataset'], kwargs['analysis']) + context['favorites']['documents']
        context['favids']['documents'] = [fav['fav'].document.id for fav in context['favorites']['documents']]
        
        return context
