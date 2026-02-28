# -*- coding: utf-8 -*-
"""
Template tags for product specifications
"""
from django import template
from product.models import ProductSpecificationValue

register = template.Library()


@register.simple_tag
def get_product_specs(product):
    """Get all specification values for a product"""
    return ProductSpecificationValue.objects.filter(product=product)


@register.filter
def get_spec_value(product, spec_name):
    """Get a specific specification value for a product"""
    try:
        return ProductSpecificationValue.objects.get(
            product=product,
            specification__name=spec_name
        ).value
    except ProductSpecificationValue.DoesNotExist:
        return None
