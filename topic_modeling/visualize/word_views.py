
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
from django.template import Context

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common import BreadCrumb, paginate_list, \
    WordSummary, WordFindForm, get_word_list
from topic_modeling.visualize.models import Dataset, Word

def index(request, dataset, analysis, word):
    context = Context()
    context['highlight'] = 'words_tab'
    context['tab'] = 'word'
    context['baseurl'] = '/datasets/%s/analyses/%s/words' % (dataset,
            analysis)
    context['dataset'] = dataset
    context['analysis'] = analysis
    dataset = Dataset.objects.get(name=dataset)
    analysis = dataset.analysis_set.get(name=analysis)
    
    words = get_word_list(request, dataset.name)
    
    num_per_page = request.session.get('words-per-page', 30)
    page_num = request.session.get('word-page', 1)
    words, num_pages, _ = paginate_list(words, page_num, num_per_page)
        
    context['words'] = words
    context['num_pages'] = num_pages
    context['page_num'] = page_num
    
    if word:
        context['curword'] = Word.objects.get(dataset=dataset, type=word)
    else:
        context['curword'] = context['words'][0]

    context['breadcrumb'] = BreadCrumb()
    context['breadcrumb'].dataset(dataset)
    context['breadcrumb'].analysis(analysis)
    context['breadcrumb'].word(context['curword'])
    
    add_word_charts(dataset, analysis, context)
    
    word_base = request.session.get('word-find-base', '')
    context['word_find_form'] = WordFindForm(word_base)
        
    add_word_contexts(context['curword'].type, context['baseurl'], context)
#    word = context['curword'].type
#    words = []
#    for i in range(0,10):
#        w = WordSummary(word, number=i)
#        w.url = context['baseurl'] + word
#        words.append(w)
#    
#    context['word_contexts'] = words
        
    return render_to_response('word.html', context)

def add_word_charts(dataset, analysis, context):
    topicwords = context['curword'].topicword_set.filter(
            topic__analysis=analysis)
    total = reduce(lambda x, tw: x + tw.count, topicwords, 0)
    topics = sorted([WordSummary(tw.topic.name, float(tw.count) / total)
            for tw in topicwords])
    topics.sort()
    context['topic_chart_address'] = get_chart(topics)
    
    docwords = context['curword'].documentword_set.filter(
            document__dataset=dataset)
    total = reduce(lambda x, dw: x + dw.count, docwords, 0)
    docs = sorted([WordSummary(dw.document.filename, float(dw.count) / total)
                   for dw in docwords])
    context['doc_chart_address'] = get_chart(docs)

def add_word_contexts(word, base_url, context):
    word_url = base_url + word
    words = []
    for i in range(0,10):
        w = WordSummary(word, number=i)
        w.url = word_url
        words.append(w)
    
    context['word_contexts'] = words