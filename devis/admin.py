from django.contrib import admin
from .models import Quote, QuoteItem
from django.contrib.auth import get_user_model

class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    fields = ('product', 'quantity', 'price', 'rate', 'tax')
    raw_id_fields = ('product',)

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client',  'date_expiration', 'total_amount', 'status', 'completed')
    list_filter = ('status', 'created_at', 'date_expiration', 'completed')
    search_fields = ('numero', 'client__name', 'quote_terms')
    readonly_fields = ('numero', 'created_at', 'total_amount')
    raw_id_fields = ('client', 'created_by')
    inlines = [QuoteItemInline]

    fieldsets = (
        (None, {
            'fields': ('numero', 'client',  'date_expiration', 'created_by')
        }),
        ('Détails financiers', {
            'fields': ('total_amount', 'status', 'completed')
        }),
        ('Informations supplémentaires', {
            'fields': ('quote_terms',),
            'classes': ('collapse',)
        }),
    )
    # Methods

    
    actions = ['marquer_comme_envoye', 'marquer_comme_accepte', 'marquer_comme_refuse']

    def marquer_comme_envoye(self, request, queryset):
        updated = queryset.update(statut='envoyé')
        self.message_user(request, f'{updated} devis ont été marqués comme envoyés.')
    marquer_comme_envoye.short_description = "Marquer les devis sélectionnés comme envoyés"

    def marquer_comme_accepte(self, request, queryset):
        updated = queryset.update(statut='accepté')
        self.message_user(request, f'{updated} devis ont été marqués comme acceptés.')
    marquer_comme_accepte.short_description = "Marquer les devis sélectionnés comme acceptés"

    def marquer_comme_refuse(self, request, queryset):
        updated = queryset.update(statut='refusé')
        self.message_user(request, f'{updated} devis ont été marqués comme refusés.')
    marquer_comme_refuse.short_description = "Marquer les devis sélectionnés comme refusés"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('client', 'created_by')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouveau devis
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not change:
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()
        form.instance.update_total_amount()

@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('quote', 'product', 'quantity', 'price', 'rate', 'tax', 'get_subtotal')
    list_filter = ('quote',)
    search_fields = ('product__name', 'quote__numero')
    raw_id_fields = ('quote', 'product')

    def get_subtotal(self, obj):
        return obj.quantity * obj.price
    get_subtotal.short_description = 'Sous-total'
