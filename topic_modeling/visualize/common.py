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
from topic_modeling.visualize.models import Word

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
    
    def add(self, text, url):
        self.items.append(BreadCrumbItem(text, url))

    def dataset(self, dataset):
        self._add_item('datasets', 'Dataset', dataset.name, dataset.name)

    def analysis(self, analysis):
        self._add_item('analyses', 'Analysis', analysis.name, analysis.name)

    def topic(self, topic_number, topic_name):
        self._add_item('topics', 'Topic', topic_number, topic_name)

    def word(self, word):
        self._add_item('words', 'Word', word.type, word.type)

    def document(self, document):
        self._add_item('documents', 'Document', document.id, document.id)

    def attribute(self, attribute):
        self._add_item('attributes', 'Attribute', attribute.name,
                attribute.name)

    def value(self, value):
        self._add_item('values', 'Value', value.value, value.value)

    def plot(self):
        # This one is different because plots currently just use posts, not
        # urls, to change
        self.currenturl += '/plots'
        text = 'Plot'
        self.items.append(BreadCrumbItem(text, self.currenturl))

    def _add_item(self, url_word, text_word, item_url, item_text):
        self.currenturl += '/%s/%s' % (url_word, item_url)
        text = '%s: %s' % (text_word, item_text)
        self.items.append(BreadCrumbItem(text, self.currenturl))


class BreadCrumbItem(object):
    def __init__(self, text, url):
        self.text = text
        self.url = url


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
