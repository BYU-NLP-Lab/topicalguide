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

from topic_modeling.visualize.models import TopicNameScheme, TopicName

def name_schemes(analysis):
    return TopicNameScheme.objects.filter(analysis__name=analysis).order_by('name')

def current_name_scheme_id(session, analysis):
    schemes = name_schemes(analysis)
    
    if 'current_name_scheme_id' not in session:
        current_name_scheme_id = schemes[0].id
        session['current_name_scheme_id'] = current_name_scheme_id
    else:
        current_name_scheme_id = session['current_name_scheme_id']
    return current_name_scheme_id

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