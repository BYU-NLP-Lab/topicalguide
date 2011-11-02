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

import base64
import pickle

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods, require_GET

from topic_modeling import anyjson
from topic_modeling.visualize.common.http_responses import JsonResponse
from topic_modeling.visualize.models import DatasetFavorite, Dataset, Analysis, AnalysisFavorite, TopicFavorite, Topic, \
    TopicViewFavorite
from topic_modeling.visualize.topics.names import current_name_scheme, topic_name_with_ns


@require_GET
def datasets(request):
    return JsonResponse([fav.dataset.id for fav in _dataset_favorites(request)])

def _dataset_favorites(request):
    return DatasetFavorite.objects.filter(session_key=request.session.session_key)

def dataset_favorite_entries(request):
    return [{'text':fav.dataset.readable_name,
             'url': reverse('tg-dataset', kwargs={'dataset':fav.dataset.name}),
             'favurl':reverse('tg-favs-dataset', kwargs={'dataset':fav.dataset.name}),
             'fav':fav} for fav in _dataset_favorites(request)]

@require_http_methods(['GET', 'PUT', 'DELETE'])
def dataset(request, dataset):
    dataset = Dataset.objects.get(name=dataset)
    
    def get():
        try:
            return DatasetFavorite.objects.get(dataset=dataset, session_key=request.session.session_key)
        except DatasetFavorite.DoesNotExist:
            return None
    
    def create():
        DatasetFavorite.objects.create(dataset=dataset, session_key=request.session.session_key)
    
    return _favorites_ajax_handler(request, get, create)

@require_GET
def analyses(request, **kwargs):
    if 'dataset' in kwargs:
        return JsonResponse([fav.analysis.id for fav in _analysis_favorites(request, dataset=kwargs['dataset'])])
    else:
        return JsonResponse([fav.analysis.id for fav in _analysis_favorites(request)])

def _analysis_favorites(request, dataset=None):
    if dataset:
        return AnalysisFavorite.objects.filter(session_key=request.session.session_key, analysis__dataset__name=dataset)
    else:
        return AnalysisFavorite.objects.filter(session_key=request.session.session_key)

def analysis_favorite_entries(request):
    return [{
        'text': fav.analysis.dataset.readable_name + ': ' + fav.analysis.name,
        'url': reverse('tg-analysis', kwargs={'dataset':fav.analysis.dataset.name, 'analysis':fav.analysis.name}),
        'favurl': reverse('tg-favs-analysis', kwargs={'dataset':fav.analysis.dataset.name, 'analysis':fav.analysis.name}),
        'fav': fav} for fav in _analysis_favorites(request)]

@require_http_methods(['GET', 'PUT', 'DELETE'])
def analysis(request, dataset, analysis):
    analysis = Analysis.objects.get(name=analysis, dataset__name=dataset)
    
    def get():
        try:
            return AnalysisFavorite.objects.get(analysis=analysis, session_key=request.session.session_key)
        except AnalysisFavorite.DoesNotExist:
            return None
    
    def create():
        AnalysisFavorite.objects.create(analysis=analysis, session_key=request.session.session_key)
    
    return _favorites_ajax_handler(request, get, create)

@require_GET
def topics(request, dataset, analysis):
    return JsonResponse([fav.topic.number for fav in _topic_favorites(request, dataset, analysis)])

def _topic_favorites(request, dataset=None, analysis=None):
    if dataset:
        if analysis:
            return TopicFavorite.objects.filter(topic__analysis__dataset__name=dataset, topic__analysis__name=analysis, session_key=request.session.session_key)
        else:
            return TopicFavorite.objects.filter(topic__analysis__dataset__name=dataset, session_key=request.session.session_key)
    else:
        if analysis:
            return TopicFavorite.objects.filter(topic__analysis__name=analysis, session_key=request.session.session_key)
        else:
            return TopicFavorite.objects.filter(session_key=request.session.session_key)

def favorite_topic_entries(request, dataset=None, analysis=None):
    entries = list()
    for fav in _topic_favorites(request, dataset, analysis):
        topic = fav.topic
        analysis = topic.analysis
        dataset = analysis.dataset
        ns = current_name_scheme(request.session, analysis)
        kwargs = {'dataset': dataset.name,
                  'analysis': analysis.name,
                  'topic': topic.number}
        entries.append({
                     'text': topic_name_with_ns(fav.topic, ns),
                     'url': reverse('tg-topic', kwargs=kwargs),
                     'favurl': reverse('tg-favs-topic', kwargs=kwargs),
                     'fav': fav})
    return entries

@require_http_methods(['GET', 'PUT', 'DELETE'])
def topic(request, dataset, analysis, topic):
    topic = Topic.objects.get(analysis__dataset__name=dataset, analysis__name=analysis, number=int(topic))
    
    def get():
        try:
            return TopicFavorite.objects.get(topic=topic, session_key=request.session.session_key)
        except TopicFavorite.DoesNotExist:
            return None
    
    def create():
        TopicFavorite.objects.create(topic=topic, session_key=request.session.session_key)
    
    return _favorites_ajax_handler(request, get, create)

'''
    {get} should return None if the favorite doesn't exist
'''
def _favorites_ajax_handler(request, get, create):
    fav = get()
    
    if request.method=='GET':
        if fav is not None:
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=404)
    elif request.method=='PUT':
        if not fav:
            create()
        return HttpResponse(status=201)
    elif request.method=='DELETE':
        if fav:
            fav.delete()
        return HttpResponse(status=204)
    else:
        raise Exception("Unsupported HTTP method '" + request.method + "'")


@require_GET
def topic_views(request):
    return JsonResponse([{'favid':fav.favid, 'name':fav.name, 'topic_num':fav.topic.number} for fav in _topic_view_favorites(request)])

def _topic_view_favorites(request):
    return TopicViewFavorite.objects.filter(session_key=request.session.session_key)

def topic_view_favorite_entries(request):
    entries = list()
    for fav in _topic_view_favorites(request):
        url = reverse('tg-favs-topic-view', kwargs={'favid': fav.favid})
        entries.append({
                     'text': fav.name,
                     'url': url,
                     'favurl': url,
                     'fav': fav})
    return entries

@require_http_methods(['GET', 'PUT', 'DELETE'])
def topic_view(request, favid):
    from topic_modeling.visualize.topics.views import TopicView
    if request.method=='GET':
        fav = get_object_or_404(TopicViewFavorite, favid=favid)
        filters = base64.b64decode(fav.filters)
        topic_filters = pickle.loads(filters)
        return TopicView.as_view()(request, favid, dataset=fav.topic.analysis.dataset, analysis=fav.topic.analysis, topic_filters=topic_filters)
    elif request.method=='PUT':
        params = anyjson.loads(request.read())
        dataset = Dataset.objects.get(name=params['dataset'])
        analysis = Analysis.objects.get(dataset=dataset, name=params['analysis'])
        topic = Topic.objects.get(analysis=analysis,number=params['topic'])
        name = params['name']
#        favid = params.get('favid', slugify(name))
        filters =  base64.b64encode(pickle.dumps(request.session.get('topic-filters', list())))
        TopicViewFavorite.objects.create(session_key=request.session.session_key, topic=topic, name=name, favid=favid, filters=filters)
        return HttpResponse(status=201)
    elif request.method=='DELETE':
        fav = get_object_or_404(TopicViewFavorite, favid=favid)
        fav.delete()
        return HttpResponse(status=204)

@require_GET
def document_views(request):
    pass

@require_http_methods(['GET', 'PUT', 'DELETE'])
def document_view(request, viewid):
    pass

#def index(request, dataset, analysis, id):
#    page_vars = dict()
#    page_vars['highlight'] = 'favorite_tab'
#    page_vars['tab'] = 'favorite'
#    page_vars['dataset'] = dataset
#    page_vars['analysis'] = analysis
#
#    page_vars['page_num'] = 1
#    page_vars['num_pages'] = 1
#    page_vars['favorites'] = request.session.get('favorite-set', set())
#
#    if id == '':
#        id = 0
#    else:
#        id = int(id)
#
#    page_vars['curr_favorite'] = None
#    for fav in page_vars['favorites']:
#        if fav.id == id:
#            page_vars['curr_favorite'] = fav
#
#    return render_to_response('favorite.html', page_vars)
#
#class Favorite:
#    def __init__(self, url, id, session, tab):
#        self.name = tab + ":" + url.split('/')[-1]
#        self.url = url
#        self.id = id
#        self.session_recall = {}
#        for key in session.keys():
#            if key.startswith(tab):
#                self.session_recall[key] = copy.deepcopy(session[key])
#        self.tab = tab
#
#    def __hash__(self):
#        return self.id
#
#    def __eq__(self, other):
#        return self.id == other.id
#
#    def __cmp__(self, other):
#        return self.id - other.id
#
##AJAX Calls
#def get_favorite_page(request, number):
#    ret_val = dict()
#    favorites = request.session.get('favorite-set', set())
#    ret_val['favorites'] = [{'id' : fav.id, 'name' : fav.name}
#                            for fav in favorites]
#    ret_val['num_pages'] = 1
#    ret_val['page'] = 1
#
#    return HttpResponse(anyjson.dumps(ret_val))
#
#def add_favorite(request, tab):
#    favorites = request.session.get('favorite-set', set())
#    id = request.session.get('last-favorite-id', 0)
#    url = request.GET['url']
#    favorite = Favorite(url, id, request.session, tab)
#    favorites.add(favorite)
#    request.session['last-favorite-id'] = favorite.id + 1
#    request.session['favorite-set'] = favorites
#    return HttpResponse('Favorite Added:' + favorite.url)
#
#def remove_all_favorites(request):
#    if 'favorite-set' in request.session:
#        request.session.remove('favorite-list')
#    return HttpResponse('Favorites cleared')
#
#def remove_favorite(request, url):
#    favorites = request.session.get('favorite-set', set())
#    if url in favorites:
#        favorites.remove(url)
#    request.session['favorite-set'] = favorites
#    return HttpResponse('Url Removed:' + url)
#
#def recall_favorite(request, id):
#    favorites = request.session.get('favorite-set', set())
#    id = int(id)
#    for favorite in favorites:
#        if favorite.id == id:
#            for key in favorite.session_recall.keys():
#                request.session[key] = copy.deepcopy(favorite.session_recall[key])
#            return HttpResponseRedirect(favorite.url)
#    return HttpResponse('Unknown Favorite')

