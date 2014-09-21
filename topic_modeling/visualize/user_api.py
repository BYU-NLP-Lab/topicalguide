"""
The user api is responsible for allowing users to login and retrieve stored information
such as favorites, notes, etc.
"""

from topic_modeling.visualize.models import *
from django.views.decorators.http import require_POST
from django.views.decorators.gzip import gzip_page
from django.views.decorators.cache import cache_control
from topic_modeling.visualize.common.http_responses import JsonResponse
from django.contrib.auth import authenticate, login, logout


@cache_control(private=True)
@require_POST
@gzip_page
def user_api(request):
    result = {}
    post = request.POST
    try:
        if not request.user.is_authenticated():
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
                        result['user'] = query_user_info(request.user, post)
                    else:
                        result['error'] = 'Your account has been disabled.'
                else:
                    result['error'] = 'Invalid username or password.'
        else:
            if 'logout' in post:
                logout(request)
                result['logged_in'] = False
            else:
                result['logged_in'] = True
                result['user'] = query_user_info(request.user, post)
    except Exception as e:
        result['error'] = str(e)
    return JsonResponse(result)


def query_user_info(user, options):
    return {"favorites": {}}
