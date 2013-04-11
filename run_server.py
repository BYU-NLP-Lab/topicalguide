#!/usr/bin/env python

from topic_modeling import manage

def run(cmd):
    manage.execute_manager(manage.settings, ['run_server.py', cmd])

def main():
    '''
    if manage.settings.local_settings.USE_GUNICORN:
        if manage.settings.gunicorn:
            return run('run_gunicorn')
        print "Gunicorn not installed; defaulting to normal execution"
    '''
    if manage.settings.django_extensions:
        return run('runserver_plus')
    return run('runserver')


if __name__ == '__main__':
    main()
