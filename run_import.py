#!/usr/bin/env python

import os
import sys

try:
    from import_tool.local_settings import LOCAL_DIR, build
except ImportError:
    raise Exception("Import error looking for local_settings.py. "
            "Look at import_tool/local_settings.py.sample for help")

if __name__ == '__main__':
    DB_BASE = os.path.join(LOCAL_DIR, '.dbs')
    if not os.path.exists(DB_BASE):
        os.mkdir(DB_BASE)
    sys.path.append("tools/doit")
    from doit.doit_cmd import cmd_main
    path = os.path.abspath('import_tool/backend.py')

    #The database file where we'll store info about this build
    db_name = os.path.join(DB_BASE, "{0}.db".format(build.replace('/','_')))

    args = ['-f', path] + ['--db', db_name] + sys.argv[1:]
    res = cmd_main(args)

print 'done'

# vim: et sw=4 sts=4
