#!/usr/bin/env python
import os
import sys

path = '/srv/topicalguide'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

import pprint

class LoggingMiddleware:

    def __init__(self, application):
        self.__application = application

    def __call__(self, environ, start_response):
        errors = environ['wsgi.errors']
        pprint.pprint(('REQUEST', environ), stream=errors)

        def _start_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errors)
            return start_response(status, headers, *args)

        return self.__application(environ, _start_response)


'''
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

application = app
'''
