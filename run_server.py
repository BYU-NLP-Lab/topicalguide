#!/usr/bin/env python
'''Run the Topical Guide Server

Usage:
    run_server.py [-h] [--gunicorn | --wsgi | --wsgi-plus ]

-h --help       show help
--gunicorn      run with gunicorn (dies if not available)
--wsgi          run using django's normal wsgi server
--wsgi-plus     run using werkzeug's special server, with awesome debug page

Default functionality is: if local_settings.USE_GUNICORN, try to run with
gunicorn. If not USE_GUNICORN or gunicorn isn't installed, run with werkzeug
(if it's available) otherwise use django's normal wsgi server.
'''
from topic_modeling import manage

def run(cmd):
    manage.execute_manager(manage.settings, ['run_server.py', cmd])

def plain_main():
    if getattr(manage.settings.local_settings, 'USE_GUNICORN', False):
        if manage.settings.gunicorn:
            return run('run_gunicorn')
        print "Gunicorn not installed; defaulting to normal execution"
    if manage.settings.django_extensions:
        return run('runserver_plus')
    return run('runserver')
main = plain_main

def docopt_main():
    res = docopt(__doc__, version='0.1b')
    if res['--gunicorn']:
        if manage.settings.gunicorn:
            return run('run_gunicorn')
        else:
            print "FATAL: Gunicorn not installed"
            return
    elif res['--wsgi-plus']:
        if manage.settings.django_extensions:
            return run('runserver_plus')
        else:
            print 'FATAL: django-extensions not installed. Can\'t use wsgi-plus'
            return
    elif res['--wsgi']:
        return run('runserver')
    else:
        return plain_main()

try:
    from docopt import docopt
    main = docopt_main
except ImportError:
    print "Docopt not installed. Command-line arguments disabled"

if __name__ == '__main__':
    main()
