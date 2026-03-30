from django import template

register = template.Library()

@register.filter
def after_colon(value):
    """Returns the part of a string after the first colon."""
    if ':' in value:
        return value.split(':', 1)[1].strip()
    return value
