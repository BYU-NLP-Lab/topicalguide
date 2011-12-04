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

from django.conf.urls.defaults import patterns, url
from django.conf import settings

from topic_modeling.visualize.topics.views import TopicView, TopicWordView, \
    TopicDocumentView
from topic_modeling.visualize.documents.views import DocumentView
from topic_modeling.visualize.dataset_views import DatasetView
from topic_modeling.visualize.word_views import WordView
from topic_modeling.visualize.attribute_views import AttributeDocumentView, \
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

dataset = r'datasets/(?P<dataset>[^/]+)'
dataset_nc = r'datasets/[^/]+'
analysis = r'analyses/(?P<analysis>[^/]+)'
topic = r'topics/(?P<topic>[^/]*)'
word = r'words/(?P<word>[^/]*)'
map = r'maps/(?P<namescheme>[^/]*)'
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

prefix = 'topic_modeling.visualize'

datasets_base = r'^datasets'
dataset_base = r'^' + dataset
analyses_base = dataset_base + '/analyses'
analysis_base = dataset_base + '/' + analysis

urlpatterns = patterns('',
# Dataset View
    url(r'^$', DatasetView.as_view(), name='tg-datasets'),
    url(r'^' + dataset + '$', DatasetView.as_view(), name='tg-dataset'),

# Analysis View
    url(analysis_base + '$', TopicView.as_view(), name='tg-analysis'),

# Topic Views
    url(analysis_base + '/' + topic + '$', TopicView.as_view(), name='tg-topic'),
    url(analysis_base + '/' + topic + '/' + map + '$',
        'topic_modeling.visualize.topics.views.render_topic_map', name='tg-topic-map'),
    url(analysis_base + '/' + topic + '/' + document + '$',
        TopicDocumentView.as_view(), name='tg-topic-doc'),
    url(analysis_base + '/' + topic + '/' + word + '$',
        TopicWordView.as_view(), name='tg-topic-word'),

# Attribute Views
    url(analysis_base + '/attributes$', AttributeView.as_view(), name='tg-attrs'),
    url(analysis_base + '/' + attribute + '$',
        AttributeView.as_view(), name='tg-attr'),
    url(analysis_base + '/' + attribute + '/' + value + '$',
        AttributeView.as_view(), name='tg-attr-val'),
    url(analysis_base + '/' + attribute + '/' + value + '/' + word + '$',
        AttributeWordView.as_view(), name='tg-attr-val-word'),
    url(analysis_base + '/' + attribute + '/' + value + '/' + document + '$',
        AttributeDocumentView.as_view(), name='tg-attr-val-doc'),

# Word Views
    url(analysis_base + '/words$', WordView.as_view(), name='tg-words'),
    url(analysis_base + '/' + word + '$', WordView.as_view(), name='tg-word'),

# Document Views
    url(analysis_base + '/documents$', DocumentView.as_view(), name='tg-docs'),
    url(analysis_base + '/' + document + '$', DocumentView.as_view(), name='tg-doc'),

# Plot View
    url(analysis_base + '/plots$', PlotView.as_view(), name='tg-plots'),
    url(analysis_base + '/' + plot + '$', PlotView.as_view(), name='tg-plot')
)

feeds_base = 'feeds'

urlpatterns += patterns(prefix + '.ajax_calls',
# AJAX Calls
    (r'^feeds/word-in-context/' + dataset + '/' + analysis + '/' + word + '$',
        'word_in_context'),
    (r'^feeds/word-in-context/' + dataset + '/' + analysis + '/' + topic + '/' + word + '$',
        'word_in_context'),
    (r'^feeds/set-current-name-scheme/(?P<name_scheme>[^/]*)$',
        'set_current_name_scheme'),
# Topic-Attribute Plots
    (r'^feeds/topic-attribute-plot/' + attribute + '/' + value + '/' + topic + '$',
        'topic_attribute_plot'),
    (r'^feeds/topic-attribute-csv/' + attribute + '/' + value + '/' + topic + '$',
        'topic_attribute_csv'),
    (r'^feeds/attribute-values/' + dataset_nc + '/' + attribute + '$',
        'attribute_values'),
# Topic-Metric Plots
    (r'^feeds/topic-metric-plot/' + dataset + '/' + analysis + '/' + metric + '$',
        'topic_metric_plot'),
# Words
    (r'^feeds/word-page/' + dataset + '/' + analysis + '/' + number + '$',
        'get_word_page'),
    (r'^feeds/word-page-find/' + dataset + '/' + analysis + '/' + word + '$',
        'update_word_page'),
# Attributes
    (r'^feeds/attribute-page/' + dataset + '/' + analysis + '/' + attribute + '/'\
           + number + '$',
        'get_attribute_page')
)

urlpatterns += patterns(prefix + '.topics.ajax',
# Topics
    (r'^feeds/topic-ordering/' + dataset + '/' + analysis + '/' + order_by + '$',
        'topic_ordering'),
    (r'^feeds/attrvaltopic/' + dataset + '/' + analysis + '/' + topic + '/' + attribute + \
            '/' + order_by + '$',
        'top_attrvaltopic'),
    (r'^feeds/topic-page/' + dataset + '/' + analysis + '/' + number + '$',
        'topic_page'),
    (r'^feeds/similar-topics/' + dataset + '/' + analysis + '/' + topic + '/' + measure + '$',
        'similar_topics'),
    (r'^feeds/rename-topic/' + dataset + '/' + analysis + '/' + topic + '/' + name + '$',
        'rename_topic'),
# Topic Groups
    (r'^feeds/create_topic_group/' + dataset + '/' + analysis + '/' + name + '$',
        'create_topic_group'),
    (r'^feeds/remove_topic_group/' + number + '$',
        'remove_topic_group'),
    (r'^feeds/add_topic_to_group/' + dataset + '/' + analysis + '/' + \
        number + '/' + addnumber + '$',
        'add_topic_to_group'),
    (r'^feeds/remove_topic_from_group/' + dataset + '/' + analysis + '/' + \
        number + '/' + addnumber + '$',
        'remove_topic_from_group'),
# Topic Filters
    (r'^feeds/new-topic-filter/' + dataset + '/' + analysis + '/' + topic + '/' + name + '$',
        'new_topic_filter'),
    (r'^feeds/remove-topic-filter/' + dataset + '/' + analysis + '/' + topic + '/'\
          + number + '$',
        'remove_topic_filter'),
    (r'^feeds/update-topic-attribute-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + attribute + '$',
        'update_topic_attribute_filter'),
    (r'^feeds/update-topic-attribute-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + attribute + '/' + value + '$',
        'update_topic_attribute_filter'),
    (r'^feeds/update-topic-metric-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + metric + '$',
        'update_topic_metric_filter'),
    (r'^feeds/update-topic-metric-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + metric + '/' + comp + '/' + value + '$',
        'update_topic_metric_filter'),
    (r'^feeds/update-topic-document-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + document + '$',
        'update_topic_document_filter'),
    (r'^feeds/update-topic-word-filter/' + dataset + '/' + analysis + '/' + topic + \
            '/' + number + '/' + word + '$',
        'update_topic_word_filter'),
)

# Documents
urlpatterns += patterns(prefix + '.documents.ajax',
    (r'^feeds/document-ordering/' + dataset + '/' + analysis + '/' + order_by + '$',
        'document_ordering'),
    (r'^feeds/document-page/' + dataset + '/' + analysis + '/' + document + '/' + number + '$',
        'get_document_page'),
    (r'^feeds/similar-documents/' + dataset + '/' + analysis + '/' + document + '/' + \
            measure + '$',
        'similar_documents'),
    (r'^feeds/new-document-filter/' + dataset + '/' + analysis + '/' + document + '/' + \
            name + '$',
        'new_document_filter'),
    (r'^feeds/remove-document-filter/' + dataset + '/' + analysis + '/' + document + '/'\
          + number + '$',
        'remove_document_filter'),
    (r'^feeds/update-document-topic-filter/' + dataset + '/' + analysis + '/' + document + \
            '/' + number + '/' + topic + '$',
        'update_document_topic_filter'),
    (r'^feeds/update-document-attribute-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + attribute + '$',
        'update_document_attribute_filter'),
    (r'^feeds/update-document-attribute-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + attribute + '/' + value + '$',
        'update_document_attribute_filter'),
    (r'^feeds/update-document-metric-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + metric + '/' + '$',
        'update_document_metric_filter'),
    (r'^feeds/update-document-metric-filter/' + dataset + '/' + analysis + '/' + \
            document + '/' + number + '/' + metric + '/' + comp + '/' + value + '$',
        'update_document_metric_filter'),
)

# Favorites
favs_prefix = 'topic_modeling.visualize.favorites'
item_id = r'/(?P<item_id>[^/]+)'

urlpatterns += patterns(favs_prefix,
    url('^datasets.favs$', 'datasets', name='tg-favs-datasets'),
    url(r'^' + dataset + '/fav$', 'dataset', name='tg-favs-dataset'),
    url(r'^' + dataset + '/documents.favs$', 'documents', name='tg-favs-docs'),
    url(r'^' + dataset + '/' + analysis + '/' + document + '/fav$', 'document', name='tg-favs-doc'),
    url(r'^' + dataset + '/analyses.favs$', 'analyses', name='tg-favs-analyses'),
    url(r'^' + dataset + '/' + analysis + '/fav$', 'analysis', name='tg-favs-analysis'),
    url(r'^' + dataset + '/' + analysis + '/topics.favs$', 'topics', name='tg-favs-topics'),
    url(r'^' + dataset + '/' + analysis + '/' + topic + '/fav$', 'topic', name='tg-favs-topic'),
    url(r'^favs/topics$', 'topic_views', name='tg-favs-topic-views'),
    url(r'^favs/docs$', 'document_views', name='tg-favs-doc-views'),
    url(r'^favs/topics/(?P<favid>[^/]+)$', 'topic_view', name='tg-favs-topic-view'),
    url(r'^favs/docs/(?P<favid>[^/]+)$', 'document_view', name='tg-favs-doc-view')
)

urlpatterns += patterns('',
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
