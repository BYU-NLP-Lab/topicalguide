#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

import os


def create_dir(directory):
    """\
    Ensures that the directory exists.
    """
    if not os.path.exists(directory):
        os.mkdir(directory)



# vim: et sw=4 sts=4
