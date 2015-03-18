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
import topicalguide.settings as settings
from topicalguide.settings import BASE_DIR

"""
TEST_LIST is a dict of test name to test directory information.
Example:

TEST_LIST = {
    'a' : {
        'BASE_DIR' : os.path.join(BASE_DIR, 'a'),
        'TEMPLATE_DIR' : 'templates',
        'TEMPLATE' : 'root.html',
        'VIEW_PACKAGE' : 'a.root.root',
    }
}

This example creates a test at http://example.edu/a/
It uses the full path to BASE_DIR/a/ as the base directory for all files needed by this test's template and view
The templates for the test are in BASE_DIR/a/templates/
The template to test is BASE_DIR/a/templates/root.html
The package name of the view that is rendering that template is a.root.root.
    (In other words it is the function root() at BASE_DIR/a/root.py)
"""
TEST_LIST = {
}

# this adds the template paths to the global site settings, so that the Django loader can find them
new_template_dirs = [os.path.join(TEST_LIST[i]['BASE_DIR'], TEST_LIST[i]['TEMPLATE_DIR']) for i in TEST_LIST]
settings.TEMPLATE_DIRS.extend(new_template_dirs)

