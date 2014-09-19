# Django settings for topic_modeling project.

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

import os
import sys


DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROFILE_LOG_BASE = 'topic_modeling/profiles'

ADMINS = (
    # ('Administrator', 'admin@example.com'),
)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)


USE_GUNICORN = False

# this is the path to the default sqlite database e.g.: TOPICAL_GUIDE_ROOT/working/tg.sqlite3
DB_FILE = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../working')), 'tg.sqlite3')
DB_OPTIONS = {
    'sqlite3': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_FILE
    },
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'USER': '',
        'SERVER': 'localhost',
        'PASSWORD': '',
        'NAME': ''
    },
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',                      
        'USER': '',
        'PASSWORD': '',
        'HOST': ''
    }
}

MANAGERS = ADMINS


DATABASES = {
    'default': DB_OPTIONS['sqlite3'],
}

DATASET_TO_DATABASE_MAPPING = {}

def get_keys_to_compare(engine):
    """
    Returns the main keys required to determine if a database is identical.
    """
    keys_to_check = ['NAME']
    if engine == 'django.db.backends.mysql' or \
       engine == 'django.db.backends.postgresql_psycopg2' or \
       engine == 'django.db.backends.oracle':
        additional_keys = ['USER', 'PASSWORD', 'HOST', 'PORT']
        keys_to_check.append(additional_keys)
    return keys_to_check

def is_database_config_equal(database_id, database_config):
    """
    Determine if the database configurations are identical (or close enough.)
    """
    if DATABASES[database_id]['ENGINE'] == database_config['ENGINE']:
        keys_to_check = get_keys_to_compare(database_config['ENGINE'])
        for k in keys_to_check:
            if not (k in DATABASES[database_id] and \
                    k in database_config and \
                    DATABASES[database_id][k] == database_config[k]):
                return False
        return True
            
    return False

def is_database_config_present(database_config):
    """
    Determine if the given configurations are already present in DATABASES.
    Return None if they aren't present.
    Return the key to the configurations if they are present.
    """
    for database_id in DATABASES:
        if is_database_config_equal(database_id, database_config):
            return database_id
    return None

def database_type(database_id='default'):
    """Return the type of the database as a string, ex: 'sqlite3'."""
    engine = DATABASES[database_id]['ENGINE']
    if engine == 'django.db.backends.sqlite3':
        return 'sqlite3'
    elif engine == 'django.db.backends.mysql':
        return 'mysql'
    elif engine == 'django.db.backends.postgresql_psycopg2':
        return 'postgres'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Denver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Path to the directory containing statically served files
_base_dir = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_ROOT = os.path.join(_base_dir, 'templates')
STATICFILES_ROOT = os.path.join(_base_dir, 'media')
SCRIPTS_ROOT = os.path.join(STATICFILES_ROOT, 'scripts')
STYLES_ROOT = os.path.join(STATICFILES_ROOT, 'styles')
ALLOWED_INCLUDE_ROOTS = (SCRIPTS_ROOT, STYLES_ROOT)
STATIC_URL = STATICFILES_ROOT + '/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'topic_modeling.profiling_middleware.ProfileMiddleware',
    'topic_modeling.routers.DatabaseRouterMiddleware',
)

ROOT_URLCONF = 'topic_modeling.urls'

BASE_DIR = os.path.dirname(__file__)

TEMPLATE_DIRS = (os.path.join(BASE_DIR, '../topic_modeling/templates'))

INSTALLED_APPS = (
    'topic_modeling.visualize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
    'django.contrib.staticfiles',
)

try:
    import django_extensions
    INSTALLED_APPS += ('django_extensions',)
except ImportError:
    #~ print 'Notice: django_extensions not installed. runserver_plus not available'
    django_extensions = False

try:
    import debug_toolbar
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
except ImportError:
    print 'Notice: debug_toolbar not installed.'

try:
    import gunicorn
    INSTALLED_APPS += ('gunicorn',)
except ImportError:
    #~ print 'Notice: gunicorn not installed.'
    gunicorn = False

INTERNAL_IPS = '127.0.0.1',

SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-topicalguide'
    }
}

# Database router
DATABASE_ROUTERS = ['topic_modeling.routers.DatabaseRouter']

