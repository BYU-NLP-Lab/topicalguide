from __future__ import division, print_function, unicode_literals
from django.conf.urls import patterns, include, url
from visualize import root, api, user_api

urlpatterns = patterns('',
    url(r'^$', root.root, name='root'),
    url(r'^terms$', root.terms, name='terms'),
    url(r'^api$', api.api, name='api'),
    url(r'^user_api$', user_api.user_api, name='user_api'),
)
