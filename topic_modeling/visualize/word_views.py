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

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common import BreadCrumb, paginate_list, \
    WordSummary, WordFindForm, get_word_list, Tab, Widget, AnalysisBaseView
from topic_modeling.visualize.models import Word


class WordView(AnalysisBaseView):
    template_name = 'words.html'
    def get_context_data(self, request, **kwargs):
        context = super(WordView, self).get_context_data(request, **kwargs)
        dataset = context['dataset']
        analysis = context['analysis']
        word = kwargs['word']
        
        context['highlight'] = 'words_tab'
        context['tab'] = 'word'
        
        words = get_word_list(request, dataset.name)
        
        num_per_page = request.session.get('words-per-page', 30)
        page_num = request.session.get('word-page', 1)
        words, num_pages, _ = paginate_list(words, page_num, num_per_page)
            
        context['words'] = words
        context['num_pages'] = num_pages
        context['page_num'] = page_num
        
        if word:
            word = Word.objects.get(dataset=dataset, type=word)
        else:
            word = context['words'][0]
    
        context['word'] = word
        context['breadcrumb'] = BreadCrumb().item(dataset).item(analysis).item(word)
        
        word_url = context['words_url'] + '/' + word.type
        word_base = request.session.get('word-find-base', '')
        context['word_find_form'] = WordFindForm(word_base)
        
        context['view_description'] = "Word '{0}'".format(word.type)
        
        context['tabs'] = [words_tab(analysis, word, word_url)]
        
        return context

def words_tab(analysis, word, word_url):
    tab = Tab('Word Information')
    
    tab.add(top_documents_widget(analysis.dataset, word))
    tab.add(top_topics_widget(analysis, word))
    tab.add(total_count_widget(word))
    tab.add(word_in_context_widget(word, word_url))
    
    return tab

def top_documents_widget(dataset, word):
    w = Widget('Top Documents', 'words/top_documents')
    docwords = word.documentword_set.filter(
            document__dataset=dataset)
    total = reduce(lambda x, dw: x + dw.count, docwords, 0)
    docs = sorted([WordSummary(dw.document.filename, float(dw.count) / total)
                   for dw in docwords])
    w['chart_url'] = get_chart(docs)
    return w

def top_topics_widget(analysis, word):
    w = Widget('Top Topics', 'words/top_topics')
    topicwords = word.topicword_set.filter(
            topic__analysis=analysis)
    total = reduce(lambda x, tw: x + tw.count, topicwords, 0)
    topics = sorted([WordSummary(tw.topic.name, float(tw.count) / total)
            for tw in topicwords])
    topics.sort()
    w['chart_url'] = get_chart(topics)
    return w

def total_count_widget(word):
    w = Widget('Total Count', 'words/total_count')
    w['word'] = word
    return w

def word_in_context_widget(word, word_url):
    w = Widget('Word In Context', 'words/word_in_context')
    words = []
    for i in range(0,5):
        ws = WordSummary(word.type, number=i)
        ws.url = word_url
        words.append(ws)
    
    w['word_contexts'] = words
    return w