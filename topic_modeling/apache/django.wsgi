import os
import sys

path = '/srv/topicalguide'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'topic_modeling.settings')

import django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
