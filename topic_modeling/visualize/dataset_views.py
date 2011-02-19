#!/usr/bin/env python

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


from django.shortcuts import render_to_response

from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.common import BreadCrumb, root_context
from topic_modeling.visualize.common import paginate_list

def index(request, dataset="", analysis=""):
    page_vars = root_context(dataset, analysis)
    page_vars['highlight'] = 'datasets_tab'

    datasets = Dataset.objects.all()
    page_num = 1
    datasets, num_pages, _ = paginate_list(datasets, page_num, 20)
    page_vars['datasets'] = Dataset.objects.all()
    page_vars['num_pages'] = num_pages
    page_vars['page_num'] = page_num

    if dataset:
        page_vars['dataset'] = dataset
        dataset = Dataset.objects.get(name=dataset)
    else:
        dataset = page_vars['datasets'][0]
        page_vars['dataset'] = dataset.name

    # This is probably not the right way to handle this, but it works for now.
    # The problem is that if we have filters up and switch analyses or datasets,
    # it breaks things.  TODO(matt): fix this sometime.
    request.session.clear()

    page_vars['curdataset'] = dataset

    page_vars['analyses'] = dataset.analysis_set.all()

    if analysis:
        page_vars['curanalysis'] = dataset.analysis_set.get(name=analysis)
        page_vars['analysis'] = analysis
    elif page_vars['analyses']:
        page_vars['curanalysis'] = page_vars['analyses'][0]
        page_vars['analysis'] = page_vars['curanalysis'].name

    page_vars['breadcrumb'] = BreadCrumb()
    page_vars['breadcrumb'].dataset(dataset)
    if 'curanalysis' in page_vars:
        page_vars['breadcrumb'].analysis(page_vars['curanalysis'])

    return render_to_response('datasets.html', page_vars)


# vim: et sw=4 sts=4
