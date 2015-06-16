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
from __future__ import division, print_function, unicode_literals
import sys
import time
import json
from django.core.cache import cache # Get the 'default' cache.
from django.views.decorators.http import require_GET
from django.views.decorators.gzip import gzip_page
from django.http import HttpResponse
from django.views.decorators.cache import cache_control, patch_cache_control
from django.db import connections
from topicalguide import settings
from api_versions import api_v1

DEBUG = settings.DEBUG
ALLOW_CACHING = not DEBUG and False # Change to false while debugging the api

API_VERSIONS = {
    'v1': api_v1,
}

LATEST_API_VERSION = api_v1

@gzip_page
@require_GET
def api(request, cacheable_request=False):
    """
    This is the main gateway for retrieving data.
    Only publicly available data is accessible through this api.
    """
    # Variables used to control caching
    DJANGO_CACHE_KEY_LENGTH_LIMIT = 250
    path = request.get_full_path()
    
    if len(path) <= DJANGO_CACHE_KEY_LENGTH_LIMIT and cache.has_key(path) and ALLOW_CACHING: # Check the cache.
        if DEBUG: print('API request hit cache.')
        response = HttpResponse(cache.get(path), content_type='application/json')
    else:
        start_time = time.time()
        
        # Determine the api to use
        api_version_to_use = api_v1 # Set to the latest version by default
        if 'version' in request.GET:
            requested_api_version = request.GET['version']
            api_version_to_use = API_VERSIONS.setdefault(requested_api_version, api_version_to_use)
        
        
        unfiltered_options = request.GET
        cacheable_request = not (('datasets' in unfiltered_options and unfiltered_options['datasets'] == '*') or \
                                ('analyses' in unfiltered_options and unfiltered_options['analyses'] == '*'))
        
        if DEBUG:
            con = connections['default']
            query_count = len(con.queries)
        
        # Generate the response.
        result = {}
        try:
            result = api_version_to_use.query_api(unfiltered_options)
        except Exception as e:
            result['error'] = str(e)
            if DEBUG:
                raise
        
        # SERVER CACHING
        # Don't cache anything requesting all datasets or all analyses.
        # Requests for all datasets/analyses are not cached so new versions can be detected.
        # Requests for all datasets/analyses are limited so this won't cause the server to get bogged down.
        total_time = time.time() - start_time
        
        
        if len(path) <= DJANGO_CACHE_KEY_LENGTH_LIMIT and cacheable_request and ALLOW_CACHING:
            cache.set(path, json.dumps(result))
        
        if DEBUG:
            stats = {}
            stats['query_count'] = len(con.queries) - query_count
            stats['queries'] = con.queries[query_count:]
            stats['total_time'] = total_time
            result['debug_stats'] = stats
            print('API request hit server.')
        response = HttpResponse(json.dumps(result, indent=4), content_type='application/json')
    
    # CACHING USING HEADERS
    if cacheable_request and ALLOW_CACHING:
        # Set upstream caching. Caches must revalidate every 24 hours.
        patch_cache_control(response, public=True, must_revalidate=True, max_age=60*60*24)
    else:
        patch_cache_control(response, private=True)
    
    return response
