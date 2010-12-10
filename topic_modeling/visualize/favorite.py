from django.shortcuts import render_to_response

# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.


def index(request, dataset, analysis):
    page_vars = dict()
    page_vars['highlight'] = 'favorite_tab'
    page_vars['tab'] = 'favorite'
    page_vars['dataset'] = dataset
    page_vars['analysis'] = analysis

    page_vars['page_num'] = 1
    page_vars['num_pages'] = 1
    page_vars['favorites'] = request.session.get('favorite-list',
                                                 ['abc', '123'])

    return render_to_response('favorite.html', page_vars)
