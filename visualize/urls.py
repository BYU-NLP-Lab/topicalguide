from django.conf.urls import patterns, include, url
from visualize import root, api

urlpatterns = patterns('',
    url(r'^$', root.root, name='root'),
    url(r'^terms$', root.terms, name='terms'),
    url(r'^api$', api.api, name='api'),
)
