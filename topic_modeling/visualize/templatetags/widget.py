'''
Created on Jun 9, 2011

@author: Josh Hansen
'''
from django import template

from topic_modeling.visualize.common.ui import Widget

register = template.Library()
quotes = ('"',"'")

@register.tag(name='widget')
def compile_widget_tag(_parser, token):
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