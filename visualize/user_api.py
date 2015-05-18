"""
The user api is responsible for allowing users to login and retrieve stored information
such as favorites, notes, etc.
"""
from __future__ import division, print_function, unicode_literals
import json
import traceback
from visualize.models import *
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.gzip import gzip_page
from django.views.decorators.cache import cache_control
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from visualize.api_utilities import get_list_filter, filter_csv_to_list, get_filter_int, filter_to_json, filter_nothing, filter_request



# Specify how to filter the incoming request by "key: filter_function" pairs.
# The filter_function must throw an error on invalid values or return sanitized values.
OPTIONS_FILTERS = {
    'username': filter_nothing,
    'password': filter_nothing,
    'dataset': filter_nothing,
    'metadata_type': filter_to_json,
    'dataset_add': get_list_filter(['document_metadata_type']),
    'csrfmiddlewaretoken': filter_nothing,
}


@cache_control(private=True)
@require_POST
@gzip_page
@ensure_csrf_cookie
def user_api(request):
    result = {}
    post = request.POST
    try:
        #~ if not request.user.is_authenticated():
            #~ if 'username' not in post or 'password' not in post:
                #~ result['error'] = 'Try logging in before using this api.'
            #~ else:
                #~ username = post['username']
                #~ password = post['password']
                #~ user = authenticate(username=username, password=password)
                #~ if user is not None:
                    #~ if user.is_active:
                        #~ login(request, user)
                        #~ result['logged_in'] = True
                        #~ result['success'] = 'You successfully logged in.'
                        #~ result['user'] = query_user_info(request.user, post)
                    #~ else:
                        #~ result['error'] = 'Your account has been disabled.'
                #~ else:
                    #~ result['error'] = 'Invalid username or password.'
        #~ else:
            #~ if 'logout' in post:
                #~ logout(request)
                #~ result['logged_in'] = False
            #~ else:
                #~ options = filter_request(post, OPTIONS_FILTERS)
                #~ print(options)
                #~ print('here'*20)
                #~ result['logged_in'] = True
                #~ result['user'] = query_user_info(request.user, options)
                #~ result['update'] = update_dataset(options)
                
        # TODO uncomment the above, and delete the below for security reasons
        authenticated = request.user.is_authenticated() 
        if not authenticated:
            if 'username' not in post or 'password' not in post:
                result['error'] = 'Try logging in before using this api.'
            else:
                username = post['username']
                password = post['password']
                user = authenticate(username=username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        result['logged_in'] = True
                        result['success'] = 'You successfully logged in.'
                        result['added'] = query_user_info(request.user, post)
                        authenticated = True
                    else:
                        result['error'] = 'Your account has been disabled.'
                else:
                    result['error'] = 'Invalid username or password.'
        if authenticated:
            if 'logout' in post:
                logout(request)
                result['logged_in'] = False
            else:
                options = filter_request(post, OPTIONS_FILTERS)
                result['logged_in'] = True
                result['user'] = query_user_info(request.user, options)
                result['added'] = dataset_add(options)
    except Exception as e:
        result['error'] = str(e)+":"+traceback.format_exc()
    
    response = HttpResponse(json.dumps(result, indent=4), content_type='application/json')
    
    return response


def query_user_info(user, options):
    return {"favorites": {}}

def dataset_add(options):
    print(options)
    result = {}
    if 'dataset' in options:
        dataset_name = options['dataset']
        result['dataset'] = dataset_name
        added = {}
        result['dataset_add'] = added
        dataset_db = Dataset.objects.get(name=dataset_name)
        if 'document_metadata_type' in options['dataset_add']:
            if 'metadata_type' in options:
                metadata_type = options['metadata_type']
                name = metadata_type['name']
                datatype = metadata_type['datatype']
                metadata_type_db, created = MetadataType.objects.get_or_create(name=name, datatype=datatype)
                doc_mdt_db, created2 = DatasetEmptyDocumentMetadataType.objects.get_or_create(dataset=dataset_db, metadata_type=metadata_type_db)
                added['document_metadata_type'] = {
                    "success": True,
                    "created": created || created2,
                }
    
    return result

