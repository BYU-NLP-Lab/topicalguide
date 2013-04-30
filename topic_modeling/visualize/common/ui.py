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

# Common User Interface Elements

import os
import sys

from django import forms, template
from django.template.context import Context
from django.template.defaultfilters import slugify

from topic_modeling.visualize.models import (Dataset, Analysis,
        WordType, Document, DocumentMetaInfo, DocumentMetaInfoValue)
#    Attribute, Value
from topic_modeling import settings

class FilterForm(forms.Form):
    def __init__(self, possible_filters, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.filters = []
        self.fields['f'] = forms.ChoiceField(possible_filters)
        self.fields['f'].widget.attrs['onchange'] = 'add_new_filter()'

    def add_filter(self, filter_):
        self.filters.append(filter_)

    def add_filter_form(self):
        ret_val = '<td>Add a filter by</td>'
        f = forms.forms.BoundField(self, self.fields['f'], 'filter')
        ret_val += '<td>' + f.as_widget() + '</td>'
        return ret_val

    def __unicode__(self):
        ret_val = ''
        if self.filters:
            for filter_ in self.filters:
                ret_val += '<tr>%s</tr>' % filter_.form()
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
        elif isinstance(obj, Dataset):
            self.dataset(obj)
        elif isinstance(obj, Analysis):
            self.analysis(obj)
#        elif isinstance(obj, Topic):
#            self.topic(obj)
        elif isinstance(obj, WordType):
            self.word_type(obj)
        elif isinstance(obj, Document):
            self.document(obj)
        elif isinstance(obj, DocumentMetaInfo):
            self.document_meta_info(obj)
            # self.text(obj.name)
        elif isinstance(obj, DocumentMetaInfoValue):
            self.document_meta_info_value(obj)
            # self.text(str(obj.value()))
            # TODO fix this
        #elif isinstance(obj, Attribute):
            #self.attribute(obj)
        #elif isinstance(obj, Value):
            #self.value(obj)
        else:
            raise Exception("The breadcrumb doesn't know how to handle that type of object")
        return self
    
    def text(self, text):
        self.items.append(BreadCrumbItem(None, text, text))

    def document_meta_info(self, info):
        url = '/attributes/' + info.name
        text = info.name # TODO: do we have a readable name for MetaInfo?
        tooltip = "Attribute '%s' (id=%d)" % (text, info.id)
        self._add_item(url, text, tooltip)
        return self

    def document_meta_info_value(self, value):
        url = '/values/%s' % value.value()
        text = str(value.value())
        tooltip = "Value '%s'" % text
        self._add_item(url, text, tooltip)
        return self
    
    def dataset(self, dataset):
        url = '/datasets/'+dataset.name
        text = dataset.readable_name
        tooltip = "Dataset '{0}' (id={1})".format(dataset.readable_name, dataset.id)
        self._add_item(url, text, tooltip)
        return self

    def analysis(self, analysis):
        url = '/analyses/' + analysis.name
        text = analysis.readable_name
        tooltip = "Analysis '{0}' (id={1})".format(analysis.readable_name, analysis.id)
        self._add_item(url, text, tooltip)
        return self

    def topic(self, topic_number, topic_name):
        url = '/topics/' + str(topic_number)
        text = "Topic '{0}'".format(topic_name)
        tooltip = text + " (number={0})".format(topic_number)
        self._add_item(url, text, tooltip)
        return self

    def word_type(self, word_type):
        if not word_type.type:
            raise Exception
        url = '/words/' + word_type.type
        text = "Word '"+word_type.type+"'"
        tooltip = text + " (id={0})".format(word_type.id)
        self._add_item(url, text, tooltip)
        return self

    def document(self, document):
        self._add_item('/documents/' + document.dataset.name, document.get_title(), "Document '"+document.filename+"', id="+ str(document.id))
        return self

    def attribute(self, attribute):
        self._add_item('/attributes/'+attribute.name, 'Attribute "'+attribute.name+'"', 'Attribute: '+attribute.name)
        return self

    def value(self, value):
        self._add_item('/values/'+value.value, value.value, 'Value: '+value.value)
        return self

    def plots(self):
        self._add_item('/plots', 'Plots', 'Plots')
#        # This one is different because plots currently just use posts, not
#        # urls, to change
#        self.currenturl += '/plots'
#        text = 'Plot'
#        self.items.append(BreadCrumbItem(text, self.currenturl))
        return self

    def _add_item(self, url_component, text, tooltip):
        self.currenturl += url_component
        self.items.append(BreadCrumbItem(self.currenturl, text, tooltip))
    
    def to_ul(self):
        html = ''
        
        for item in self.items[:-1]:
            html += item.to_li()
            html += '\n'
        
        html += self.items[-1:][0].to_li(last=True)
        
        return html

class BreadCrumbItem(object):
    def __init__(self, url, text, tooltip):
        self.url = url
        self.text = text
        self.tooltip = tooltip
    
    def to_li(self, last=False):
        html = '<li class="breadcrumb">'
        if last:
            html += '<span title="{0}">{1}</span>'.format(self.tooltip, self.text)
        else:
            html += '<a href="{0}" title="{1}">{2}</a></li>'.format(self.url, self.tooltip, self.text)
        html += '</li>'
        return html

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
        self.fields['find_word'].widget.attrs['onchange'] = 'find_word("'+word+'")'

class Tab(object):
    def __init__(self, title, path=None, tab_name=None, widgets=None):
        self.title = title
        
        if path:
            _style_path = '%s/tabs/%s.css' % (settings.STYLES_ROOT, path)
            if os.path.exists(_style_path):
                self.style_url = '/site-media/styles/tabs/%s.css' % path
            
            _template_path = 'tabs/%s.html' % path
            if os.path.exists('%s/%s' % (settings.TEMPLATES_ROOT, _template_path)):
                self.template_path = _template_path
            else:
                self.template_path = None
                
            _script_path = '%s/tabs/%s.js' % (settings.SCRIPTS_ROOT, path)
            if os.path.exists(_script_path):
                self.script_url = '/site-media/scripts/tabs/%s.js' % path
        
        self.widgets = widgets if widgets else dict()
    
    def add(self, widget):
        self.widgets[widget.short_path.replace('-','_')] = widget
        return self
    
    def __unicode__(self):
        if self.template_path:
            t = template.loader.get_template(self.template_path)
            ctxt = Context()
            ctxt['_tab'] = self
            ctxt['_widgets'] = self.widgets
            ctxt.update(self.widgets)
            return t.render(ctxt)
        else:
            return '\n'.join([w.__unicode__() for w in self.widgets.values()])

class Widget(object):
    def __init__(self, title, path, html=None, context=None, content_html=None):
        self.title = title
        self.path = path
        self.short_path = path.split('/')[-1:][0]
        
        self.template_path = 'widgets/%s.html' % path
        
        _script_path = '%s/widgets/%s.js' % (settings.SCRIPTS_ROOT, path)
        self.script_path = _script_path
        if os.path.exists(_script_path):
            self.script_url = '/site-media/scripts/widgets/%s.js' % path
        else:
            print>>sys.stderr, "Failed to find script file:", _script_path
        
        _style_path = '%s/widgets/%s.css' % (settings.STYLES_ROOT, path)
        if os.path.exists(_style_path):
            self.style_url = '/site-media/styles/widgets/%s.css' % path
        
        if content_html and not html:
            html = '<div id="widget-'+slugify(self.short_path)+'" class="ui-widget">\n'
            if title:
                html += '<div class="ui-widget-header">%s</div>' % title
            html += '<div class="ui-widget-content">%s</div>' % content_html
            html += '</div>'
        self.html = html
        
        self.context = context if context else Context()
        self.context['widget'] = self

    
    def __unicode__(self):
        return self.render(None)
    
    def render(self, _context):
        if self.html:
            return self.html
        else:
            t = template.loader.get_template(self.template_path)
            return t.render(self.context)
    
    def __getitem__(self, key):
        return self.context[key]
    
    def __setitem__(self, key, value):
        self.context[key] = value

class Cloud(object):
    def __init__(self, name, html):
        self.name = name
        self.html = html
