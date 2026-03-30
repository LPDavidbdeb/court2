from django import template
import pprint

register = template.Library()

@register.filter(name='is_list')
def is_list(value):
    return isinstance(value, list)

@register.filter(name='pprint')
def pprint_filter(value):
    return pprint.pformat(value)
