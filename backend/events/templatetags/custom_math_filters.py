# your_app/templatetags/custom_math_filters.py
from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtracts the arg from the value."""
    try:
        return value - arg
    except (ValueError, TypeError):
        try:
            return value - int(arg)
        except (ValueError, TypeError):
            return '' # Or raise an error, or return value, depending on desired behavior for invalid types

@register.filter
def add(value, arg):
    """Adds the arg to the value."""
    try:
        return value + arg
    except (ValueError, TypeError):
        try:
            return value + int(arg)
        except (ValueError, TypeError):
            return ''