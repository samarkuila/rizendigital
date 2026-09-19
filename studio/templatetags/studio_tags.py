from django import template
from django.forms import widgets
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag
def st_active(request, name, *args):
    """Return 'is-active' when the request is inside the given Studio section."""
    try:
        base = reverse(name, args=args)
    except NoReverseMatch:
        return ''
    path = request.path
    if name == 'studio:dashboard':
        return 'is-active' if path == base else ''
    return 'is-active' if path.startswith(base) else ''


@register.filter
def field_type(bound):
    w = bound.field.widget
    if isinstance(w, widgets.CheckboxInput):
        return 'checkbox'
    if isinstance(w, widgets.FileInput):
        return 'file'
    if isinstance(w, widgets.HiddenInput):
        return 'hidden'
    if isinstance(w, widgets.Textarea):
        return 'textarea'
    if isinstance(w, (widgets.Select, widgets.SelectMultiple)):
        return 'select'
    return 'text'


@register.filter
def dget(d, key):
    try:
        return d.get(key, '')
    except AttributeError:
        return ''


@register.filter
def initials(user):
    name = (user.get_full_name() or user.get_username() or '?').strip()
    parts = name.replace('@', ' ').replace('.', ' ').split()
    return ''.join(p[0] for p in parts[:2]).upper() or '?'
