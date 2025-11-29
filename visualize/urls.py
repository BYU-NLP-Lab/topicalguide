from django.urls import path
from visualize import root, api

urlpatterns = [
    path('', root.root, name='root'),
    path('terms', root.terms, name='terms'),
    path('api', api.api, name='api'),
]
