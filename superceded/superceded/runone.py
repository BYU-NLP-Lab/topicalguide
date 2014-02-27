#!/usr/bin/env python
'''
This is a helper module for working with the "backend.py", which, as a doit
script, requires a bit of finageling to make it easy to work with in an
interactive environment.

Usage (from within ipython):

    >>> from import_tool.runone import *
    >>> run.task_my_task(clean=True)
    # currently *ignores* dependencies

'''

import backend
import shlex
from subprocess import call
from types import GeneratorType

tasks = [x for x in dir(backend) if x.startswith('task')]

def get(task):
    res = task()
    if isinstance(res, GeneratorType):
        return list(res)
    else:
        return res

def run(task, clean=True):
    if clean and 'clean' in task:
        for item in task['clean']:
            if type(item) in (list, tuple):
                if callable(item[0]):
                    item[0](*item[1])
                else:
                    for part in item:
                        try:
                            call(shlex.split(part))
                        except:
                            pass
            elif callable(item):
                item()
    for item in task['actions']:
        if callable(item):
            item()
        elif type(item) in (list, tuple):
            item[0](*item[1])
        else:
            raise RuntimeError("Can't run {}".format(item))

def makerun(task):
    def meta(clean=True):
        return run(task, clean)
    return meta

for name in tasks:
    task = get(getattr(backend, name))
    if type(task) == list:
        for subtask in task:
            setattr(run, name + '_' + subtask['name'], makerun(subtask))
    else:
        setattr(run, name, makerun(task))


# vim: et sw=4 sts=4
