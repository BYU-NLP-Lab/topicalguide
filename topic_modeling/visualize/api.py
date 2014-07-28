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

from topic_modeling.visualize.models import *
from django.views.decorators.http import require_GET
from django.views.decorators.gzip import gzip_page
from topic_modeling.visualize.common.http_responses import JsonResponse



@gzip_page
@require_GET
def api(request):
    GET = request.GET
    result = {}
    try:
        if 'datasets' in GET:
            result['datasets'] = query_datasets(GET)
    except Exception as e:
        result['error'] = str(e)
    return JsonResponse(result)

def query_datasets(GET):
    """Gather the information for each dataset listed."""
    datasets = {}
    dataset_fields = set(get_list(GET, 'dataset_attr'))
    
    if GET['datasets'] == '*':
        datasets_queryset = Dataset.objects.filter(visible=True)
    else:
        datasets_queryset = Dataset.objects.filter(name__in=get_list(GET, 'datasets'), visible=True)
    datasets_queryset.select_related()
    
    for dataset in datasets_queryset:
        datasets[dataset.identifier] = dataset.fields_to_dict(dataset_fields)
        
        if 'analyses' in GET:
            datasets[dataset.identifier]['analyses'] = query_analyses(GET, dataset)
    return datasets

def query_analyses(GET, dataset):
    analyses = {}
    analysis_fields = set(get_list(GET, 'analysis_attr'))
    
    if GET['datasets'] == '*':
        analyses_queryset = Analysis.objects.filter(dataset=dataset)
    else:
        analyses_queryset = Analysis.objects.filter(dataset=dataset, name__in=get_list(GET, 'analyses'))
    analyses_queryset.select_related()
    
    for analysis in analyses_queryset:
        analyses[analysis.identifier] = analysis.fields_to_dict(analysis_fields)
        
        if 'topics' in GET:
            analyses[analysis.identifier]['topics'] = query_topics(GET, dataset, analysis)
    
    return analyses
    
def query_topics(GET, dataset, analysis):
    topics = {}
    topic_attr = set(get_list(GET, 'topic_attr'))
    
    if GET['topics'] == '*':
        topics_queryset = Topic.objects.filter(analysis=analysis)
    else:
        topics_queryset = Topic.objects.filter(analysis=analysis, number__in=get_list(GET, 'topics'))
    topics_queryset.select_related()
    
    for topic in topics_queryset:
        attributes = topic.attributes_to_dict(topic_attr)
        if 'words' in GET and 'top_n_words' in GET:
            attributes['words'] = topic.top_n_words(get_list(GET, 'words'), int(GET['top_n_words']))
        topics[topic.identifier] = attributes
    
    return topics

def get_list(get, key):
    if key not in get:
        return []
    elif get[key] == '*':
        return '*'
    return get[key].split(',')

