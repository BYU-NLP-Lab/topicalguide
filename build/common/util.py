#!/usr/bin/env python


def create_dirs_and_open(filename):
    """This assumes that you want to open the file for writing.  It doesn't
    make much sense to create directories if you are not going to open for
    writing."""
    try:
        return open(filename, 'w')
    except IOError as e:
        import errno
        if e.errno != errno.ENOENT:
            raise
    directory = filename.rsplit('/', 1)[0]
    try_makedirs(directory)
    return open(filename, 'w')


def try_makedirs(path):
    """Do the equivalent of mkdir -p."""
    import os
    try:
        os.makedirs(path)
    except OSError, e:
        import errno
        if e.errno != errno.EEXIST:
            raise


# vim: et sw=4 sts=4
