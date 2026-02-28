# -*- coding: utf-8 -*-
"""
Template tags for product specifications
"""
from django import template
from django.contrib.contenttypes.models import ContentType
from product.models import ProductSpecificationValue

register = template.Library()


@register.simple_tag
def get_product_specs(product):
    """Get all specification values for a product using GenericForeignKey"""
    content_type = ContentType.objects.get_for_model(product)
    return ProductSpecificationValue.objects.filter(
        product_content_type=content_type,
        product_object_id=product.pk
    )


@register.filter
def get_spec_value(product, spec_name):
    """Get a specific specification value for a product using GenericForeignKey"""
    try:
        content_type = ContentType.objects.get_for_model(product)
        spec_value = ProductSpecificationValue.objects.get(
            product_content_type=content_type,
            product_object_id=product.pk,
            specification__name=spec_name
        )
        return spec_value.value
    except ProductSpecificationValue.DoesNotExist:
        return None
