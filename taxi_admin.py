# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Category, MPCategory, Document, GDocument, TaggedItem, Commentaire, Result, Tag, Categoryy, Vote, ProductAttribute, ProductAttributeValue


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
    date_hierarchy = 'created_at'


@admin.register(MPCategory)
class MPCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'is_active',
        'parent',
        'lft',
        'rght',
        'tree_id',
        'level',
    )
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'document',
        'do_title',
        'do_description',
        'file_basename',
        'thumbnail_file',
        'file_type',
        'file_size',
        'initial_name',
        'created',
        'active',
    )
    list_filter = ('created', 'active')


@admin.register(GDocument)
class GDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'created', 'content_type', 'object_id')
    list_filter = ('document', 'created', 'content_type')


@admin.register(TaggedItem)
class TaggedItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag', 'content_type', 'object_id')
    list_filter = ('content_type',)


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'description',
        'created',
        'user_assignee',
        'current_status',
        'content_type',
        'object_id',
    )
    list_filter = ('created', 'user_assignee', 'content_type')


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'content_type', 'object_id')
    list_filter = ('content_type',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug')
    search_fields = ('slug',)


@admin.register(Categoryy)
class CategoryyAdmin(admin.ModelAdmin):
    list_display = ('id', 'parent', 'title', 'slug', 'photo')
    list_filter = ('parent', 'photo')
    search_fields = ('slug',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'owner', 'created')
    list_filter = ('content_type', 'owner', 'created')


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'value', 'product_attribute', 'position')
    list_filter = ('product_attribute',)
