
from os.path import abspath, join, dirname

# this is the directory to store the metadata and database stuff we create
LOCAL_DIR = abspath(join(dirname(__file__), '../working'))

# and this is the path of the sqlite database
DB_FILE = join(LOCAL_DIR, 'tg.sqlite3')

DBTYPE = 'sqlite3'

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
DB_CONFIG = DB_OPTIONS[DBTYPE]
SQLITE_CONFIG = DB_OPTIONS['sqlite3']
MYSQL_CONFIG = DB_OPTIONS['mysql']

USE_GUNICORN = True
