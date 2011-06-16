'''
Created on Jun 9, 2011

@author: Josh Hansen
'''

import os
from copy import copy

from django import template

from topic_modeling import settings
from topic_modeling.visualize.common import Widget

register = template.Library()
quotes = ('"',"'")

@register.tag(name='widget')
def compile_widget_tag(parser, token):
    try:
        tag_name, widget_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    
    if bool(widget_name[0] in quotes) != bool(widget_name[-1] in quotes):
        raise template.TemplateSyntaxError("%r tag's argument is quoted improperly" % tag_name)
    
    if widget_name[0] in quotes:
        return Widget(widget_name=widget_name[1:-1])
    else:
        return Widget(widget_name=widget_name)

#class WidgetNode(template.Node):
#    def __init__(self, widget_name):
#        self.widget_name = widget_name
#    
#
#    
#    def render(self, context):
#        ctxt = copy(context)
#        script_path = self._script_path()
#        if os.path.exists('%s/scripts/%s' % (settings.STATICFILES_ROOT, script_path)):
#            ctxt['widget_script_path'] = script_path
#        
#        style_path = self._style_path()
#        if os.path.exists(style_path):
#            ctxt['widget_style_url'] = self._style_url()
#        
#        t = template.loader.get_template(self._template_path())
#        return t.render(ctxt)