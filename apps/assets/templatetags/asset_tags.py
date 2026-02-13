from django import template
from ..models import AssetLocation

register = template.Library()

@register.simple_tag
def get_location_children(location):
    return AssetLocation.objects.filter(parent=location).order_by('code', 'id')

@register.filter
def has_children(location):
    return AssetLocation.objects.filter(parent=location).exists()

@register.filter(name='getattr')
def getattr_filter(obj, attr_name):
    if obj is None:
        return ''
    try:
        return getattr(obj, attr_name, '')
    except:
        return ''
