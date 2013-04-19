import os
import sys

path = '/src/topicalguide'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
