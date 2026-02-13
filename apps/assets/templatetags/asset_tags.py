from django import template
from ..models import AssetLocation, AssetCategory

register = template.Library()

@register.simple_tag
def get_location_children(location):
    return AssetLocation.objects.filter(parent=location).order_by('sort', 'code', 'id')

@register.simple_tag
def get_category_children(category):
    return AssetCategory.objects.filter(parent=category).order_by('sort', 'code', 'id')

@register.filter
def has_children(location):
    return AssetLocation.objects.filter(parent=location).exists()

@register.filter
def has_category_children(category):
    return AssetCategory.objects.filter(parent=category).exists()

@register.filter(name='getattr')
def getattr_filter(obj, attr_name):
    if obj is None:
        return ''
    try:
        return getattr(obj, attr_name, '')
    except:
        return ''
