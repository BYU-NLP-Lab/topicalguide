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

import time
from git import Repo
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.views.decorators.gzip import gzip_page
from django.views.decorators.cache import never_cache


@never_cache
@gzip_page
def root(request, *args, **kwargs):
    STATIC = '/static'
    context = {}
    context['MEDIA'] = STATIC
    context['SCRIPTS'] = STATIC + '/scripts'
    context['STYLES'] = STATIC + '/styles'
    context['IMAGES'] = STATIC + '/images'
    context['FONTS'] = STATIC + '/fonts'
    context['license'] = "http://www.gnu.org/licenses/agpl.html"
    context['wiki_url'] = "https://github.com/BYU-NLP-Lab/topicalguide/wiki"
    context['nlp_lab_url'] = "https://facwiki.cs.byu.edu/nlp/index.php/Main_Page"
    context['cs_dept_url'] = "https://cs.byu.edu"
    context['nlp_lab_logo_url'] = context['IMAGES'] + "/byunlp-135px.png"
    context['nlp_lab_small_logo_url'] = context['IMAGES'] + "/byunlp-35px.png"
    try:
        context['last_updated'] = "Last updated on %s" % time.strftime("%A, %d %B %Y %l:%M %P", time.gmtime(Repo(__file__).head.commit.committed_date))
    except:
        context['last_updated'] = "Last updated info not available."

    version = 'Version not available.'
    try:
        tags = Repo(__file__).tags
        if tags:
            version = unicode(tags[-1])
    except:
        pass
    context['version'] = version
    
    template = loader.get_template('root.html')
    template_context = RequestContext(request, context)
    return HttpResponse(template.render(template_context))

@never_cache
@gzip_page
def terms(request, *args, **kwargs):
    template = loader.get_template('terms.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))

#~ @never_cache
#~ @gzip_page
#~ def rootdev(request, *args, **kwargs):
    #~ STATIC = '/static'
    #~ context = {}
    #~ context['MEDIA'] = STATIC
    #~ context['SCRIPTS'] = STATIC + '/scripts'
    #~ context['STYLES'] = STATIC + '/styles'
    #~ context['IMAGES'] = STATIC + '/images'
    #~ context['FONTS'] = STATIC + '/fonts'
    #~ context['license'] = "http://www.gnu.org/licenses/agpl.html"
    #~ context['wiki_url'] = "https://github.com/BYU-NLP-Lab/topicalguide/wiki"
    #~ context['nlp_lab_url'] = "https://facwiki.cs.byu.edu/nlp/index.php/Main_Page"
    #~ context['cs_dept_url'] = "https://cs.byu.edu"
    #~ context['nlp_lab_logo_url'] = context['IMAGES'] + "/byunlp-135px.png"
    #~ context['nlp_lab_small_logo_url'] = context['IMAGES'] + "/byunlp-35px.png"
    #~ context['last_updated'] = "Last updated on %s" % time.strftime("%A, %d %B %Y %l:%M %P", time.gmtime(Repo(__file__).head.commit.committed_date))
    #~ 
    #~ template = loader.get_template('rootdev.html')
    #~ template_context = RequestContext(request, context)
    #~ return HttpResponse(template.render(template_context))
