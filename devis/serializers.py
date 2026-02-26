from rest_framework import serializers
from .models import Quote, QuoteItem


class QuoteItemSerializer(serializers.ModelSerializer):
    """Serializer for quote items."""
    product_name = serializers.CharField(
        source='product.name', read_only=True
    )
    product_slug = serializers.CharField(
        source='product.slug', read_only=True
    )
    subtotal = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = QuoteItem
        fields = [
            'id', 'quote', 'product', 'product_name', 'product_slug',
            'quantity', 'price', 'rate', 'tax', 'subtotal'
        ]


class QuoteSerializer(serializers.ModelSerializer):
    """Full serializer for Quote model."""
    client_name = serializers.CharField(
        source='client.user.username', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    items = QuoteItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'numero', 'created_at', 'created_by',
            'date_expiration', 'client', 'client_name',
            'total_amount', 'status', 'status_display',
            'completed', 'quote_terms',
            'items', 'item_count'
        ]
        read_only_fields = ['id', 'numero', 'created_at']
    
    def get_item_count(self, obj):
        """Return the number of items in the quote."""
        return obj.items.count()
    
    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant total doit être supérieur à zéro."
            )
        return value


class QuoteListSerializer(serializers.ModelSerializer):
    """Simplified serializer for quote list views."""
    client_name = serializers.CharField(
        source='client.user.username', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'numero', 'created_at', 'client_name',
            'total_amount', 'status', 'status_display',
            'completed', 'item_count'
        ]
    
    def get_item_count(self, obj):
        """Return the number of items in the quote."""
        return obj.items.count()


class QuoteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating quotes."""
    
    class Meta:
        model = Quote
        fields = [
            'date_expiration', 'client', 'total_amount',
            'status', 'completed', 'quote_terms'
        ]
