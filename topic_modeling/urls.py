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

from django.conf.urls.defaults import patterns
from django.conf import settings

from topic_modeling.visualize.topics.views import TopicView, TopicWordView,\
    TopicDocumentView
from topic_modeling.visualize.documents.views import DocumentView
from topic_modeling.visualize.dataset_views import DatasetView
from topic_modeling.visualize.word_views import WordView
from topic_modeling.visualize.attribute_views import AttributeDocumentView,\
    AttributeWordView, AttributeView

from topic_modeling.cssmin import cssmin
from django.http import HttpResponse
from topic_modeling.visualize.plot_views import PlotView

def render_style(request, style_path):
    css = open(settings.STYLES_ROOT + '/' + style_path).read() 
    css = cssmin(css)
    
    if style_path.endswith(".css"):
        mimetype = "text/css"
    elif style_path.endswith(".png"):
        mimetype = "image/png"
    else:
        mimetype = None
    
    return HttpResponse(css, mimetype=mimetype)

def render_script(request, script_path):
    script = open('%s/%s' % (settings.SCRIPTS_ROOT, script_path)).read()
    return HttpResponse(script, mimetype="text/javascript")

dataset = r'datasets/(?P<dataset>[^/]*)'
analysis = r'analyses/(?P<analysis>[^/]*)'
topic = r'topics/(?P<topic>[^/]*)'
word = r'words/(?P<word>[^/]*)'
map = r'maps/(?P<namescheme>[^/]+)'
attribute = r'attributes/(?P<attribute>[^/]*)'
value = r'values/(?P<value>[^/]*)'
plot = r'plots/(?P<plot>[^/]*)'
chart_type = r'chart-types/(?P<chart_type>[^/]*)'
document = r'documents/(?P<document>[^/]*)'
num_words = r'num-words/(?P<num_words>[^/]*)'
order_by = r'order-by/(?P<order_by>[^/]*)'
number = r'number/(?P<number>[^/]*)'
addnumber = r'addnumber/(?P<addnumber>[^/]*)'
name = r'name/(?P<name>[^/]*)'
metric = r'metrics/(?P<metric>[^/]*)'
measure = r'measures/(?P<measure>[^/]*)'
comp = r'comps/(?P<comp>[^/]*)'
tab = r'tab/(?P<tab>[^/]*)'
id = r'id/(?P<id>[^/]*)'

urlpatterns = patterns('',
# Dataset View
    (r'^$', DatasetView.as_view()),
    (r'^' + dataset + '$', DatasetView.as_view()),

# Analysis View
#    (r'^' + dataset + '/' + analysis + '$',
#        'topic_modeling.visualize.dataset_views.index'),
    (r'^' + dataset + '/' + analysis + '$', TopicView.as_view()),

# Topic Views
    (r'^' + dataset + '/' + analysis + '/' + topic + '$', TopicView.as_view()),
    (r'^' + dataset + '/' + analysis + '/' + topic + '/' + map + '$',
        'topic_modeling.visualize.topics.views.render_topic_map'),
    (r'^' + dataset + '/' + analysis + '/' + topic + '/' + document + '$',
        TopicDocumentView.as_view()),
    (r'^' + dataset + '/' + analysis + '/' + topic + '/' + word + '$',
        TopicWordView.as_view()),

# Attribute Views
    (r'^' + dataset + '/' + analysis + '/' + attribute + '$',
        AttributeView.as_view()),
    (r'^' + dataset + '/' + analysis + '/' + attribute + '/' + value + '$',
        AttributeView.as_view()),
    (r'^' + dataset + '/' + analysis + '/' + attribute + '/' + value + '/' + word + '$',
        AttributeWordView.as_view()),
    (r'^' + dataset + '/' + analysis + '/' + attribute + '/' + value + '/' + document + '$',
        AttributeDocumentView.as_view()),

# Word Views
    (r'^' + dataset + '/' + analysis + '/' + word + '$', WordView.as_view()),

# Document Views
    (r'^' + dataset + '/' + analysis + '/' + document + '$', DocumentView.as_view()),

# Favorite Views
    (r'^favorite/' + dataset + '/' + analysis + '/' + id + '$',
     'topic_modeling.visualize.favorite.index'),

# Plot View
    (r'^' + dataset + '/' + analysis + '/' + plot + '$',
        PlotView.as_view()),

# AJAX Calls
    (r'^feeds/word-in-context/' + dataset + '/' + analysis + '/' + word + '$',
        'topic_modeling.visualize.ajax_calls.word_in_context'),
    (r'^feeds/word-in-context/' + dataset + '/' + analysis + '/' + topic + '/' + word + '$',
        'topic_modeling.visualize.ajax_calls.word_in_context'),
    (r'^feeds/set-current-name-scheme/(?P<name_scheme>[^/]*)$',
        'topic_modeling.visualize.ajax_calls.set_current_name_scheme'),
# Topic-Attribute Plots
    (r'^feeds/topic-attribute-plot/' + attribute + '/' + value + '/' + topic + '$',
        'topic_modeling.visualize.ajax_calls.topic_attribute_plot'),
    (r'^feeds/attribute-values/' + dataset + '/' + attribute + '$',
        'topic_modeling.visualize.ajax_calls.attribute_values'),
# Topic-Metric Plots
    (r'^feeds/topic-metric-plot/' + dataset + '/' + analysis + '/' + metric + '$',
        'topic_modeling.visualize.ajax_calls.topic_metric_plot'),
# Topics
    (r'^feeds/topic-ordering/' + dataset + '/' + analysis + '/' + order_by + '$',
        'topic_modeling.visualize.topics.ajax.topic_ordering'),
    (r'^feeds/attrvaltopic/' + dataset + '/' + analysis + '/' + topic + '/' + attribute + \
            '/' + order_by + '$',
        'topic_modeling.visualize.topics.ajax.top_attrvaltopic'),
    (r'^feeds/topic-page/' + dataset + '/' + analysis + '/' + number + '$',
        'topic_modeling.visualize.topics.ajax.get_topic_page'),
    (r'^feeds/similar-topics/' + dataset + '/' + analysis + '/' + topic + '/' + measure + '$',
        'topic_modeling.visualize.topics.ajax.similar_topics'),
    (r'^feeds/rename-topic/' + dataset + '/' + analysis + '/' + topic + '/' + name + '$',
        'topic_modeling.visualize.topics.ajax.rename_topic'),
# Topic Groups
    (r'^feeds/create_topic_group/' + dataset + '/' + analysis + '/' + name + '$',
        'topic_modeling.visualize.topics.ajax.create_topic_group'),
    (r'^feeds/remove_topic_group/' + number + '$',
        'topic_modeling.visualize.topics.ajax.remove_topic_group'),
    (r'^feeds/add_topic_to_group/' + dataset + '/' + analysis + '/' + \
        number + '/' + addnumber + '$',
        'topic_modeling.visualize.topics.ajax.add_topic_to_group'),
    (r'^feeds/remove_topic_from_group/' + dataset + '/' + analysis + '/' + \
        number + '/' + addnumber + '$',
        'topic_modeling.visualize.topics.ajax.remove_topic_from_group'),
# Topic Filters
    (r'^feeds/new-topic-filter/' + dataset + '/' + analysis + '/' + topic + '/' + name + '$',
        'topic_modeling.visualize.topics.ajax.new_topic_filter'),
    (r'^feeds/remove-topic-filter/' + dataset + '/' + analysis + '/' + topic + '/'\
          + number + '$',
        'topic_modeling.visualize.topics.ajax.remove_topic_filter'),
    (r'^feeds/update-topic-attribute-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + attribute + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_attribute_filter'),
    (r'^feeds/update-topic-attribute-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + attribute + '/' + value + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_attribute_filter'),
    (r'^feeds/update-topic-metric-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + metric + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_metric_filter'),
    (r'^feeds/update-topic-metric-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + metric + '/' + comp + '/' + value + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_metric_filter'),
    (r'^feeds/update-topic-document-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + document + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_document_filter'),
    (r'^feeds/update-topic-word-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + word + '$',
        'topic_modeling.visualize.topics.ajax.update_topic_word_filter'),
# Words
    (r'^feeds/word-page/' + dataset + '/' + analysis + '/' + number + '$',
        'topic_modeling.visualize.ajax_calls.get_word_page'),
    (r'^feeds/word-page-find/' + dataset + '/' + analysis + '/' + word + '$',
        'topic_modeling.visualize.ajax_calls.update_word_page'),
# Documents
    (r'^feeds/document-ordering/' + dataset + '/' + analysis + '/' + order_by + '$',
        'topic_modeling.visualize.documents.ajax.document_ordering'),
    (r'^feeds/document-page/' + dataset + '/' + analysis + '/' + document + '/' + number + '$',
        'topic_modeling.visualize.documents.ajax.get_document_page'),
    (r'^feeds/similar-documents/' + dataset + '/' + analysis + '/' + document + '/' + \
            measure + '$',
        'topic_modeling.visualize.documents.ajax.similar_documents'),
    (r'^feeds/new-document-filter/' + dataset + '/' + analysis + '/' + document + '/' + \
            name + '$',
        'topic_modeling.visualize.documents.ajax.new_document_filter'),
    (r'^feeds/remove-document-filter/' + dataset + '/' + analysis + '/' + document + '/'\
          + number + '$',
        'topic_modeling.visualize.documents.ajax.remove_document_filter'),
    (r'^feeds/update-document-topic-filter/' + dataset + '/' + analysis + '/' + document + \
            '/' + number + '/' + topic + '$',
        'topic_modeling.visualize.documents.ajax.update_document_topic_filter'),
    (r'^feeds/update-document-attribute-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + attribute + '$',
        'topic_modeling.visualize.documents.ajax.'
        'update_document_attribute_filter'),
    (r'^feeds/update-document-attribute-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + attribute + '/' + value + '$',
        'topic_modeling.visualize.documents.ajax.'
        'update_document_attribute_filter'),
    (r'^feeds/update-document-metric-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + metric + '/' + '$',
        'topic_modeling.visualize.documents.ajax.'
        'update_document_metric_filter'),
    (r'^feeds/update-document-metric-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + metric + '/' + comp + '/' + value + '$',
        'topic_modeling.visualize.documents.ajax.'
        'update_document_metric_filter'),
# Attributes
    (r'^feeds/attribute-page/' + dataset + '/' + analysis + '/' + attribute + '/'\
           + number + '$',
        'topic_modeling.visualize.ajax_calls.get_attribute_page'),
# Favorites
    (r'^feeds/add_favorite/' + tab + '$', #?url=<escaped url to save>
        'topic_modeling.visualize.ajax_calls.add_favorite'),
    (r'^feeds/recall_favorite/' + id + '$',
        'topic_modeling.visualize.ajax_calls.recall_favorite'),
    (r'^feeds/clear_favorite$',
        'topic_modeling.visualize.ajax_calls.remove_all_favorites'),
    (r'^feeds/favorite-page/' + number + '$',
        'topic_modeling.visualize.ajax_calls.get_favorite_page'),

#Styles
    (r'^styles/(?P<style_path>.+)$', render_style),
#Scripts
    (r'^scripts/(?P<script_path>.+)$', render_script),

#General Static Files
    # TODO(dan): Is this OK for production?  Would it just be a matter of
    # making sure that document root was set correctly in Apache, or is there
    # more to it?
    (r'^site-media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATICFILES_ROOT, 'show_indexes': True}),
)