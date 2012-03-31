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

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common.views import AnalysisBaseView
from topic_modeling.visualize.common.ui import BreadCrumb, WordSummary, \
    WordFindForm, Tab, Widget
from topic_modeling.visualize.common.helpers import get_word_list, paginate_list
from topic_modeling.visualize.models import WordType, Document, Topic
from topic_modeling.visualize import sess_key
from django.db.models.aggregates import Count
from topic_modeling.visualize.topics.names import current_name_scheme, topic_name_with_ns


class WordView(AnalysisBaseView):
    template_name = 'words.html'
    def get_context_data(self, request, **kwargs):
        context = super(WordView, self).get_context_data(request, **kwargs)
        dataset = context['dataset']
        analysis = context['analysis']
        word = kwargs['word'] if 'word' in kwargs else None
        
        context['highlight'] = 'words_tab'
        context['tab'] = 'word'
        
        words = get_word_list(request, dataset.name)
        
        num_per_page = request.session.get('words-per-page', 30)
        page_num = request.session.get(sess_key(dataset,'word-page'), 1)
        words, num_pages, page_num = paginate_list(words, page_num, num_per_page)
            
        context['words'] = words
        context['num_pages'] = num_pages
        context['page_num'] = page_num
        
        if word:
            word = WordType.objects.get(type=word)
        else:
            word = context['words'][0]
    
        context['word'] = word
        context['breadcrumb'] = BreadCrumb().item(dataset).item(analysis).item(word)
        
        word_url = context['words_url'] + '/' + word.type
        word_base = request.session.get(sess_key(dataset,'word-find-base'), '')
        context['word_find_form'] = WordFindForm(word_base)
        
        context['view_description'] = "Word Type '{0}'".format(word.type)
        
        context['tabs'] = [words_tab(request.session, analysis, word, word_url, context['IMAGES'])]
        
        return context

def words_tab(session, analysis, word, word_url, images_url):
    tab = Tab('Word Information', 'words/word_information')
    
    tab.add(top_documents_widget(analysis.dataset, word))
    tab.add(top_topics_widget(session, analysis, word))
    tab.add(total_count_widget(word))
    tab.add(word_in_context_widget(word, word_url, images_url))
    
    return tab

#def top_documents_widget(dataset, word):
#    w = Widget('Top Documents', 'words/top_documents')
#    docwords = word.documentword_set.filter(
#            document__dataset=dataset)
#    total = reduce(lambda x, dw: x + dw.count, docwords, 0)
#    docs = sorted([WordSummary(dw.document.filename, float(dw.count) / total)
#                   for dw in docwords])
#    w['chart_url'] = get_chart(docs)
#    return w

def top_documents_widget(dataset, word):
    w = Widget('Top Documents', 'words/top_documents')
    docs = Document.objects.raw('''select doc.*,count(*) as count
    from visualize_wordtype as type, visualize_wordtoken as token, visualize_document as doc
    where type.type=%s and token.type_id=type.id and token.document_id=doc.id group by doc.id order by count desc''', [word.type])
    total = float(sum([doc.count for doc in docs]))
    doc_summaries = [WordSummary(doc.filename, float(doc.count) / total) for doc in docs]
    w['chart_url'] = get_chart(doc_summaries)
    return w

def top_topics_widget(session, analysis, word):
    w = Widget('Top Topics', 'words/top_topics')
    analysis_tokens = word.tokens.filter(topics__analysis=analysis)
    total = float(analysis_tokens.count())
    topicwords = analysis_tokens.values('topics').annotate(count=Count('topics')).order_by('-count')
    
    ns = current_name_scheme(session, analysis)
    topics = list()
    for count_obj in topicwords:
        pct = count_obj['count'] / total
        topic = Topic.objects.get(id=count_obj['topics'])
        name = topic_name_with_ns(topic, ns)
        topics.append(WordSummary(name,pct))
#    topics = [WordSummary(Topic.objects.get(id=x['topics']).name, x['count']/total) for x in topicwords]
    
#    topicwords = word.topicword_set.filter(
#            topic__analysis=analysis)
#    total = reduce(lambda x, tw: x + tw.count, topicwords, 0)
#    topics = sorted([WordSummary(tw.topic.name, float(tw.count) / total)
#            for tw in topicwords])
#    topics.sort()
    w['chart_url'] = get_chart(topics)
    return w

def total_count_widget(word):
    w = Widget('Total Count', 'words/total_count')
    w['word'] = word
    return w

def word_in_context_widget(word, word_url, images_url):
    w = Widget('Word In Context', 'words/word_in_context')
    words = []
    for i in range(0,5):
        ws = WordSummary(word.type, number=i)
        ws.url = word_url
        words.append(ws)
    w['IMAGES'] = images_url
    w['words'] = words
    return w
