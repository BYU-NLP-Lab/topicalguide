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

from django.shortcuts import render_to_response
from topic_modeling import anyjson
from django.http import HttpResponse, HttpResponseRedirect
import copy

def index(request, dataset, analysis, id):
    page_vars = dict()
    page_vars['highlight'] = 'favorite_tab'
    page_vars['tab'] = 'favorite'
    page_vars['dataset'] = dataset
    page_vars['analysis'] = analysis

    page_vars['page_num'] = 1
    page_vars['num_pages'] = 1
    page_vars['favorites'] = request.session.get('favorite-set', set())

    if id == '':
        id = 0
    else:
        id = int(id)

    page_vars['curr_favorite'] = None
    for fav in page_vars['favorites']:
        if fav.id == id:
            page_vars['curr_favorite'] = fav

    return render_to_response('favorite.html', page_vars)

class Favorite:
    def __init__(self, url, id, session, tab):
        self.name = tab + ":" + url.split('/')[-1]
        self.url = url
        self.id = id
        self.session_recall = {}
        for key in session.keys():
            if key.startswith(tab):
                self.session_recall[key] = copy.deepcopy(session[key])
        self.tab = tab

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    def __cmp__(self, other):
        return self.id - other.id

#AJAX Calls
def get_favorite_page(request, number):
    ret_val = dict()
    favorites = request.session.get('favorite-set', set())
    ret_val['favorites'] = [{'id' : fav.id, 'name' : fav.name}
                            for fav in favorites]
    ret_val['num_pages'] = 1
    ret_val['page'] = 1

    return HttpResponse(anyjson.dumps(ret_val))

def add_favorite(request, tab):
    favorites = request.session.get('favorite-set', set())
    id = request.session.get('last-favorite-id', 0)
    url = request.GET['url']
    favorite = Favorite(url, id, request.session, tab)
    favorites.add(favorite)
    request.session['last-favorite-id'] = favorite.id + 1
    request.session['favorite-set'] = favorites
    return HttpResponse('Favorite Added:' + favorite.url)

def remove_all_favorites(request):
    if 'favorite-set' in request.session:
        request.session.remove('favorite-list')
    return HttpResponse('Favorites cleared')

def remove_favorite(request, url):
    favorites = request.session.get('favorite-set', set())
    if url in favorites:
        favorites.remove(url)
    request.session['favorite-set'] = favorites
    return HttpResponse('Url Removed:' + url)

def recall_favorite(request, id):
    favorites = request.session.get('favorite-set', set())
    id = int(id)
    for favorite in favorites:
        if favorite.id == id:
            for key in favorite.session_recall.keys():
                request.session[key] = copy.deepcopy(favorite.session_recall[key])
            return HttpResponseRedirect(favorite.url)
    return HttpResponse('Unknown Favorite')