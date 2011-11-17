#!/usr/bin/env python

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


from django import forms


# Methods
#########

def sort_documents(documents, sort_by):
    # Because of the way I had to implement metric sorting, and the way that
    # filtering is implemented, you cannot filter after you have sorted.  Be
    # sure to call this method after filtering, and before paginate_list,
    # unless you really know what you are doing.
    django_orderings = ['word_count', '-word_count', 'filename', '-filename']
    if sort_by in django_orderings:
        return documents.order_by(sort_by)
    elif 'metric:' in sort_by:
        metric_name = sort_by[7:]
        document_list = list(documents.all())
        document_list.sort(key=lambda x:
                -x.documentmetricvalue_set.get(metric__name=metric_name).value)
        return document_list
    else:
        raise ValueError("We don't currently support ordering by %s" % sort_by)


# Classes
#########

class SortDocumentForm(forms.Form):
    def __init__(self, analysis, *args, **kwargs):
        super(SortDocumentForm, self).__init__(*args, **kwargs)
        choices = []
        choices.append(('filename', 'Filename'))
        for metric in analysis.documentmetric_set.all():
            choices.append(('metric:%s' % metric.name, metric.name))
        self.fields['sort'] = forms.ChoiceField(choices, label='Sort by')
        self.fields['sort'].widget.attrs['onchange'] = 'sort_documents()'


# vim: et sw=4 sts=4
