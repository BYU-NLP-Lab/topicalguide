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

##########################
# General helper functions
##########################


from django.core.paginator import Paginator, EmptyPage
from topic_modeling.visualize.models import Dataset, Analysis, Word
from django.shortcuts import get_object_or_404
from topic_modeling.visualize.common.ui import Widget

def get_dataset_and_analysis(dataset_name, analysis_name):
    dataset = get_object_or_404(Dataset, name=dataset_name)
    analysis = get_object_or_404(Analysis, name=analysis_name, dataset=dataset)
    return dataset, analysis

def set_word_context(word, document, analysis, topic=None):
    word.left_context, word.word, word.right_context \
        = document.get_context_for_word(word.word, analysis, topic)


def paginate_list(list_, page, num_per_page, obj=None):
    # If given, obj overrides page, and we find the page that contains
    # obj
    paginator = Paginator(list_, num_per_page)
    if obj:
        for page in range(1, paginator.num_pages+1):
            list_ = paginator.page(page).object_list
            if obj in list_:
                return list_, paginator.num_pages, page
    try:
        return paginator.page(page).object_list, paginator.num_pages, page
    except EmptyPage:
        return paginator.page(1).object_list, paginator.num_pages, 1


# TODO(matt): is there a better way to do this?
def get_word_cloud(words, open_='', close='', url=True):
    #note that this only works if words is presorted by percent
    idx = 3 if len(words) > 3 else len(words) - 1
    if idx == -1:
        return ""
    scale = words[idx].percent

    def cmpWord(x, y):
        return cmp(x.word.lower(), y.word.lower())
#        return cmp(str(x.word).lower(), str(y.word).lower())
    words = sorted(words, cmpWord)

    cloud = ''
    for word in words:
        if url:
            cloud += '<a href="%s">' % word.url
        size = word.percent / scale * 100 + 50
        text = open_ + word.word.lower() + close
        cloud += '<span style="font-size:%d%%">%s</span> ' % (size, text)
        if url:
            cloud += '</a>'
    return cloud

def word_cloud_widget(words, title='Word Cloud', open_=None, close=None, url=True):
    w = Widget(title, 'common/word_cloud')
    
    if open_: w['open_text'] = open_
    if close: w['close_text'] = close
    
    #note that this only works if words is presorted by percent
    if len(words) > 3: scale = words[3].percent
    elif len(words) == 0: scale = 1.0
    else: scale = words[-1:].percent

    words = sorted(words, cmp=lambda x,y: cmp(x.word.lower(), y.word.lower()))
    
    for word in words:
        word.size = word.percent / scale * 100 + 50
    
    w['words'] = words
    
    return w

# Word tab helper functions (maybe these should be moved to a new file)
############################

def get_word_list(request, dataset_name):
    words = Word.objects.filter(dataset__name=dataset_name)
    word_base = request.session.get('word-find-base', '')
    words = filter(lambda w: w.type.startswith(word_base), words)
    return words