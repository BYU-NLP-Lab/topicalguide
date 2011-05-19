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


from django import forms
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.template.context import Context
from topic_modeling.visualize.models import Word, Dataset, Analysis, Topic,\
    Document, Attribute, Value

def root_context(dataset, analysis):
    context = Context()
    context['dataset'] = dataset
    context['analysis'] = analysis
    context['dataset_url'] = "/datasets/%s" % (dataset)
    context['analysis_url'] = "%s/analyses/%s" % (context['dataset_url'],
            analysis)

    context['attributes_url'] = context['analysis_url'] + "/attributes"
    context['documents_url'] = context['analysis_url'] + "/documents"
    context['plots_url'] = context['analysis_url'] + "/plots"
    context['topics_url'] = context['analysis_url'] + "/topics"
    context['words_url'] = context['analysis_url'] + "/words"
    return context

################################################################################
# Classes
################################################################################

# Base Filter classes
#####################

class FilterForm(forms.Form):
    def __init__(self, possible_filters, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.filters = []
        self.fields['f'] = forms.ChoiceField(possible_filters)
        self.fields['f'].widget.attrs['onchange'] = 'add_new_filter()'

    def add_filter(self, filter):
        self.filters.append(filter)

    def add_filter_form(self):
        ret_val = '<td>Add a filter by</td>'
        f = forms.forms.BoundField(self, self.fields['f'], 'filter')
        ret_val += '<td>' + f.as_widget() + '</td>'
        return ret_val

    def __unicode__(self):
        ret_val = ''
        if self.filters:
            for filter in self.filters:
                ret_val += '<tr>%s</tr>' % filter.form()
        ret_val += '<tr>%s</tr>' % self.add_filter_form()
        return ret_val


# BreadCrumb classes
####################

class BreadCrumb(object):
    """Builds a BreadCrumb incrementally.  Each method call adds another item
    to the bread crumb, in the order that the method is called."""
    def __init__(self):
        self.items = []
        self.currenturl = ''

    def __iter__(self):
        return self.items.__iter__()
    
    def item(self, obj):
        if isinstance(obj, basestring):
            self.text(obj)
        if isinstance(obj, Dataset):
            self.dataset(obj)
        elif isinstance(obj, Analysis):
            self.analysis(obj)
        elif isinstance(obj, Topic):
            self.topic(obj)
        elif isinstance(obj, Word):
            self.word(obj)
        elif isinstance(obj, Document):
            self.document(obj)
        elif isinstance(obj, Attribute):
            self.attribute(obj)
        elif isinstance(obj, Value):
            self.value(obj)
        else:
            raise("The breadcrumb doesn't know how to handle that type of object")
        return self
    
    def add(self, text, url):
        self.items.append(BreadCrumbItem(text, url))
        return self
    
    def text(self, text):
        self.items.append(BreadCrumbItem(text, None))
    
    def dataset(self, dataset):
        self.add(dataset.readable_name, '/datasets/'+dataset.name)
        return self

    def analysis(self, analysis):
        self.add(analysis.name, '/datasets/{0}/analyses/{1}'.format(analysis.dataset.name, analysis.name))
        return self

    def topic(self, topic_number, topic_name):
        self._add_item('topics', 'Topic', topic_number, topic_name)
        return self

    def word(self, word):
        self._add_item('words', 'Word', word.type, word.type)
        return self

    def document(self, document):
        self.add(document.filename, '/datasets/{0}/analyses/{1}/documents/{2}'.format(document.dataset.name, ))
        self._add_item('documents', 'Document', document.id, document.id)
        return self

    def attribute(self, attribute):
        self._add_item('attributes', 'Attribute', attribute.name,
                attribute.name)
        return self

    def value(self, value):
        self._add_item('values', value.value, value.value)
        return self

    def plot(self):
        # This one is different because plots currently just use posts, not
        # urls, to change
        self.currenturl += '/plots'
        text = 'Plot'
        self.items.append(BreadCrumbItem(text, self.currenturl))
        return self

    def _add_item(self, type, id, text, alt_text):
        self.currenturl += '/%s/%s' % (type, id)
        self.items.append(BreadCrumbItem(text, self.currenturl))
    
    def to_ul(self):
        html = ''
        
        for item in self.items[:-1]:
            html += item.to_li()
            html += '\n'
        
        html += self.items[-1:][0].to_li(last=True)
        
        return html

class BreadCrumbItem(object):
    def __init__(self, text, url):
        self.text = text
        self.url = url
    
    def to_li(self, last=False):
        html = '<li class="breadcrumb">'
        if last:
            html += '<span>{0}</span>'.format(self.text)
        else:
            html += '<a href="{0}">{1}</a></li>'.format(self.url, self.text)
        html += '</li>'
        return html


# Other classes
###############

class WordSummary(object):
    def __init__(self, word="", percent="", number=None):
        self.word = word
        self.url = ""
        self.left_context = ""
        self.right_context = ""
        self.percent = percent
        self.doc_name = ""
        self.doc_id = ""
        self.number = number

    def normalized(self, total):
        self.percent = 1. * self.count / total

    def __cmp__(self, other):
        return cmp(-float(self.percent), -float(other.percent))


class WordFindForm(forms.Form):
    def __init__(self, word, *args, **kwargs):
        super(WordFindForm, self).__init__(*args, **kwargs)
        self.fields['find_word'] = forms.CharField(max_length=100,
                initial=word)
        self.fields['find_word'].widget.attrs['onchange'] = 'find_word()'


class TopLevelWidget(object):
    def __init__(self, title):
        self.title = title
        self.ref = title.lower().replace(' ', '-')
        self.widgets = []
        self.hidden = True


class Widget(object):
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.hidden = True


class Cloud(object):
    def __init__(self, name, html):
        self.name = name
        self.html = html


################################################################################
# Helper functions
################################################################################


# General helper functions
##########################

def set_word_context(word, document, analysis, topic=None):
    right, left = document.get_context_for_word(word.word, analysis, topic)
    word.left_context = left
    word.right_context = right


def paginate_list(list, page, num_per_page, object=None):
    # If given, object overrides page, and we find the page that contains
    # object
    paginator = Paginator(list, num_per_page)
    if object:
        for page in range(1, paginator.num_pages+1):
            list = paginator.page(page).object_list
            if object in list:
                return list, paginator.num_pages, page
    return paginator.page(page).object_list, paginator.num_pages, None


# TODO(matt): is there a better way to do this?
def get_word_cloud(words, open='', close='', url=True):
    #note that this only works if words is presorted by percent
    idx = 3 if len(words) > 3 else len(words) - 1
    if idx == -1:
        return ""
    scale = words[idx].percent

    def cmpWord(x, y):
        return cmp(x.word.lower(), y.word.lower())
#        return cmp(str(x.word).lower(), str(y.word).lower())
    words = sorted(words, cmpWord)

    cloud = ""
    for word in words:
        if url:
            cloud += '<a href="%s">' % word.url
        size = word.percent / scale * 100 + 50
        text = open + word.word.lower() + close
        cloud += '<span style="font-size:%d%%">%s</span> ' % (size, text)
        if url:
            cloud += '</a>'
    return cloud


# Word tab helper functions (maybe these should be moved to a new file)
############################

def get_word_list(request, dataset_name):
    words = Word.objects.filter(dataset__name=dataset_name)
    word_base = request.session.get('word-find-base', '')
    words = filter(lambda w: w.type.startswith(word_base), words)
    return words

# vim: et sw=4 sts=4
