
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Invoice, InvoiceItem, Customer, StatutFacture

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'quantity', 'price', 'rate', 'tax')
    raw_id_fields = ('product',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'created_at', 'expiration_date', 'total_amount', 'status', 'completed')
    list_filter = ('status', 'created_at', 'expiration_date', 'completed')
    search_fields = ('numero', 'client__name', 'invoice_terms')
    readonly_fields = ('numero', 'created_at', 'invoice_total')
    fieldsets = (
        (None, {
            'fields': ('numero', 'client', 'created_at', 'expiration_date', 'created_by')
        }),
        ('Détails financiers', {
            'fields': ('total_amount', 'invoice_total', 'status', 'completed')
        }),
        ('Informations supplémentaires', {
            'fields': ('invoice_terms', 'devis_source'),
            'classes': ('collapse',)
        }),
    )
    inlines = [InvoiceItemInline]
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('client', 'devis_source', 'created_by')

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('client', 'devis_source', 'created_by')
        return self.readonly_fields

    actions = ['marquer_comme_complete', 'marquer_comme_incomplete']

    def marquer_comme_complete(self, request, queryset):
        updated = queryset.update(completed=True)
        self.message_user(request, f'{updated} factures ont été marquées comme complétées.')
    marquer_comme_complete.short_description = "Marquer les factures sélectionnées comme complétées"

    def marquer_comme_incomplete(self, request, queryset):
        updated = queryset.update(completed=False)
        self.message_user(request, f'{updated} factures ont été marquées comme incomplètes.')
    marquer_comme_incomplete.short_description = "Marquer les factures sélectionnées comme incomplètes"

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si c'est une nouvelle facture
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        form.instance.update_invoice_total()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'price', 'rate', 'tax', 'get_subtotal')
    list_filter = ('invoice',)
    search_fields = ('product__name', 'invoice__numero')
    raw_id_fields = ('invoice', 'product')

    def get_subtotal(self, obj):
        return obj.quantity * obj.price
    get_subtotal.short_description = 'Sous-total'
