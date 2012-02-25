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

from topic_modeling.visualize.models import TopicNameScheme, TopicName, Analysis
from topic_modeling.visualize import sess_key

def name_schemes(analysis):
#    if isinstance(analysis, basestring):
#        return TopicNameScheme.objects.filter(analysis__name=analysis).order_by('name')
    if isinstance(analysis, Analysis):
        return analysis.topicnamescheme_set.order_by('name')
    else:
        raise TypeError("Can only get name schemes for Analysis objects")

def current_name_scheme_id(session, analysis):
    key = sess_key(analysis.dataset,'current_name_scheme_id')
    schemes = name_schemes(analysis)
    def default():
        return schemes[0].id
        
    
    if key not in session:
        session[key] = default()
    else:
        if not analysis.topicnamescheme_set.filter(id=session[key]):
            session[key] = default()
    return session[key]

def set_current_name_scheme_id(session, dataset, name_scheme):
    key = sess_key(dataset,'current_name_scheme_id')
    session[key] = name_scheme

def current_name_scheme(session, analysis):
    ns_id = current_name_scheme_id(session, analysis)
    current_name_scheme = TopicNameScheme.objects.get(id=ns_id)
    return current_name_scheme

'''For one-off topic name requests. Usually you want to use a stored name scheme
so current_name_scheme() doesn't have to get called over an over. Still, this
method is good for modeling how topic naming works.'''
def topic_name(session, topic):
    name_scheme_id = current_name_scheme_id(session, topic.analysis)
    return topic_name_with_ns_id(topic, name_scheme_id)

'''Use this when you already know what name scheme you want'''
def topic_name_with_ns_id(topic, name_scheme_id):
    ns = TopicNameScheme.objects.get(id=name_scheme_id)
    return topic_name_with_ns(topic, ns)

def topic_name_with_ns(topic, name_scheme):
    try:
        name = TopicName.objects.get(topic=topic, name_scheme=name_scheme).name
    except:
        name = topic.name
    return name