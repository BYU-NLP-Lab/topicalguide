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

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROFILE_LOG_BASE = 'topic_modeling/profiles'

ADMINS = (
    # ('Administrator', 'admin@example.com'),
)

MANAGERS = ADMINS

#DBTYPE = 'sqlite3'
DBTYPE = 'mysql'

SQLITE_CONFIG = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'tg.sqlite3'
}
MYSQL_CONFIG = {
    'ENGINE': 'django.db.backends.mysql',
    'USER': 'topicalguide',
    'SERVER': 'localhost',
    'PASSWORD': 'topicalguide',
    'NAME': 'topicalguide_newimport'
}

DATABASES = {'default': SQLITE_CONFIG if DBTYPE=='sqlite3' else MYSQL_CONFIG}

def database_type():
    return DBTYPE

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Path to the directory containing statically served files
TEMPLATES_ROOT = os.getcwd() + '/topic_modeling/templates'
STATICFILES_ROOT = os.getcwd()+'/topic_modeling/media'
SCRIPTS_ROOT = STATICFILES_ROOT + '/scripts'
STYLES_ROOT = STATICFILES_ROOT + '/styles'
ALLOWED_INCLUDE_ROOTS = (SCRIPTS_ROOT, STYLES_ROOT)

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
#TODO Set this before deploying a server
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'topic_modeling.urls'



TEMPLATE_DIRS = ('/home/josh/Projects/topicalguide/topic_modeling/templates')

INSTALLED_APPS = (
    'topic_modeling.visualize',
#    'django.contrib.admin',
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
)

SESSION_SAVE_EVERY_REQUEST = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
