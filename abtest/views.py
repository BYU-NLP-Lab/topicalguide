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

from __future__ import print_function

from django.shortcuts import render, redirect
from django.http import HttpResponse

import abtest
from abtest.settings import TEST_LIST

from visualize import root

# Create your views here.
def test(request, arg, *args, **kwargs):
    if arg not in TEST_LIST:
        print("Error! Unknown view should have been hit instead")

    package_list = TEST_LIST[arg]['VIEW_PACKAGE'].split('.')
    view_package = package_list.pop()

    package = ".".join(package_list)
    view = getattr(__import__(package, fromlist=[view_package]), view_package)
    return view(request, args, kwargs)

# This view is called when the given url does not match anything
def unknown(request, arg, *args, **kwargs):
    # redirect to the root view
    return redirect('/')
