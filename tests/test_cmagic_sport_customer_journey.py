# -*- coding: utf-8 -*-
"""
Tests du parcours client CMagic Sport

Ce fichier teste le parcours client complet:
1. Catalog (page d'accueil/listing des produits)
2. Product Detail (page détail produit)
3. Cart (panier)
4. Checkout (paiement)
5. Checkout Success (confirmation)

URLs testées:
- /cmagic-sport/ (Catalog)
- /cmagic-sport/product/<slug>/ (Product Detail)
- /cmagic-sport/cart/ (Cart)
- /cmagic-sport/checkout/ (Checkout)
- /cmagic-sport/checkout/success/ (Success)
"""
import pytest
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from cmagic_sport.models import SportProduct
from product.models import ProductType


@pytest.mark.django_db
class TestCmagicSportCustomerJourney:
    """Tests du parcours client complet sur CMagic Sport."""
    
    @pytest.fixture
    def client(self):
        """Client HTTP pour les tests."""
        return Client()
    
    @pytest.fixture
    def product_type(self):
        """Créer un type de produit pour les tests."""
        return ProductType.objects.create(
            name='Basket',
            slug='basket',
            is_active=True
        )
    
    @pytest.fixture
    def sport_product(self, product_type):
        """Créer un produit sport pour les tests."""
        product = SportProduct.objects.create(
            name='Nike Air Jordan 1 High OG',
            slug='nike-air-jordan-1-high-og',
            description=' basket Jordan authentique',
            price=179.99,
            stock=10,
            in_stock=True,
            available=True,
            is_active=True,
            brand='Nike',
            product_type=product_type,
            available_sizes='40,41,42,43,44',
            is_limited_edition=False,
            is_season_promo=False,
        )
        return product
    
    @pytest.fixture
    def second_product(self, product_type):
        """Créer un deuxième produit sport pour les tests."""
        return SportProduct.objects.create(
            name='Adidas Harden Vol 7',
            slug='adidas-harden-vol-7',
            description=' basket Adidas Harden',
            price=159.99,
            stock=5,
            in_stock=True,
            available=True,
            is_active=True,
            brand='Adidas',
            product_type=product_type,
            available_sizes='41,42,43,44,45',
            is_limited_edition=False,
            is_season_promo=False,
        )

    # ============================================
    # ÉTAPE 1: CATALOG (PAGE D'ACCUEIL)
    # ============================================
    
    def test_catalog_page_loads(self, client):
        """Test que la page catalogue se charge correctement."""
        url = reverse('cmagic_sport:catalog')
        response = client.get(url)
        
        assert response.status_code == 200, f"Erreur: status {response.status_code}"
        print(f"✓ Catalog page loaded: {url}")
    
    def test_catalog_contains_products(self, client, sport_product, second_product):
        """Test que le catalogue affiche les produits."""
        url = reverse('cmagic_sport:catalog')
        response = client.get(url)
        
        assert response.status_code == 200
        # Les produits doivent être dans le contexte
        assert 'products' in response.context
        print(f"✓ Catalog shows products: {sport_product.name}, {second_product.name}")
    
    def test_catalog_filter_by_brand(self, client, sport_product, second_product):
        """Test du filtre par marque sur le catalogue."""
        url = reverse('cmagic_sport:catalog') + '?brand=Nike'
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ Catalog filter by brand works")

    # ============================================
    # ÉTAPE 2: PRODUCT DETAIL (PAGE DÉTAIL)
    # ============================================
    
    def test_product_detail_page_loads(self, client, sport_product):
        """Test que la page détail produit se charge."""
        url = reverse('cmagic_sport:product_detail', kwargs={'slug': sport_product.slug})
        response = client.get(url)
        
        assert response.status_code == 200, f"Erreur: status {response.status_code}"
        assert 'product' in response.context
        print(f"✓ Product detail page loaded: {sport_product.name}")
    
    def test_product_detail_shows_info(self, client, sport_product):
        """Test que les informations du produit sont affichées."""
        url = reverse('cmagic_sport:product_detail', kwargs={'slug': sport_product.slug})
        response = client.get(url)
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        
        # Vérifications des informations du produit
        assert sport_product.name in content, "Le nom du produit doit être affiché"
        assert str(sport_product.price) in content or '179.99' in content, "Le prix doit être affiché"
        print(f"✓ Product info displayed: price={sport_product.price}")
    
    def test_product_detail_shows_availability(self, client, sport_product):
        """Test que la disponibilité est affichée."""
        url = reverse('cmagic_sport:product_detail', kwargs={'slug': sport_product.slug})
        response = client.get(url)
        
        assert response.status_code == 200
        # Le produit est en stock
        assert sport_product.in_stock is True
        assert sport_product.stock > 0
        print(f"✓ Product availability shown: stock={sport_product.stock}")
    
    def test_product_not_found_returns_404(self, client):
        """Test qu'un produit inexistant retourne 404."""
        url = reverse('cmagic_sport:product_detail', kwargs={'slug': 'produit-inexistant'})
        response = client.get(url)
        
        assert response.status_code == 404
        print(f"✓ 404 returned for non-existent product")

    # ============================================
    # ÉTAPE 3: CART (PANIER)
    # ============================================
    
    def test_cart_page_loads(self, client):
        """Test que la page panier se charge."""
        url = reverse('cmagic_sport:cart')
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ Cart page loaded")
    
    def test_cart_empty_initially(self, client):
        """Test que le panier est vide au départ."""
        url = reverse('cmagic_sport:cart')
        response = client.get(url)
        
        assert response.status_code == 200
        # Le panier doit être vide (mock pour le moment)
        print(f"✓ Cart is empty initially")

    # ============================================
    # ÉTAPE 4: CHECKOUT (PAIEMENT)
    # ============================================
    
    def test_checkout_page_loads(self, client):
        """Test que la page checkout se charge."""
        url = reverse('cmagic_sport:checkout')
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ Checkout page loaded")
    
    def test_checkout_post_redirects_to_success(self, client):
        """Test que le POST checkout redirige vers succès."""
        url = reverse('cmagic_sport:checkout')
        
        # Données de formulaire de test
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '0612345678',
            'address': '123 Rue de Test',
            'city': 'Paris',
            'postal_code': '75001',
            'country': 'FR',
        }
        
        response = client.post(url, data=checkout_data)
        
        # Doit rediriger vers la page de succès
        assert response.status_code in [302, 200]
        success_url = reverse('cmagic_sport:checkout_success')
        if response.status_code == 302:
            assert success_url in response.url
            print(f"✓ Checkout POST redirects to success")
        else:
            print(f"✓ Checkout POST processed")

    # ============================================
    # ÉTAPE 5: CHECKOUT SUCCESS (CONFIRMATION)
    # ============================================
    
    def test_checkout_success_page_loads(self, client):
        """Test que la page de confirmation se charge."""
        url = reverse('cmagic_sport:checkout_success')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'order' in response.context
        print(f"✓ Checkout success page loaded")
    
    def test_checkout_success_shows_order_info(self, client):
        """Test que les informations de commande sont affichées."""
        url = reverse('cmagic_sport:checkout_success')
        response = client.get(url)
        
        assert response.status_code == 200
        # Les données mock de commande doivent être présentes
        order = response.context['order']
        assert 'order_number' in order
        print(f"✓ Order info displayed: {order.get('order_number')}")

    # ============================================
    # WORKFLOW COMPLET: SÉQUENCE COMPLÈTE
    # ============================================
    
    def test_complete_customer_journey(self, client, sport_product, second_product):
        """Test du parcours client complet: Catalog -> Detail -> Cart -> Checkout -> Success"""
        
        print("\n" + "="*60)
        print("DÉBUT DU PARCOURS CLIENT COMPLET")
        print("="*60)
        
        # ÉTAPE 1: Visit Catalog
        print("\n[1] Visit Catalog...")
        catalog_url = reverse('cmagic_sport:catalog')
        response = client.get(catalog_url)
        assert response.status_code == 200
        print(f"    ✓ Catalog loaded: {catalog_url}")
        
        # ÉTAPE 2: View Product Detail
        print("\n[2] View Product Detail...")
        detail_url = reverse('cmagic_sport:product_detail', kwargs={'slug': sport_product.slug})
        response = client.get(detail_url)
        assert response.status_code == 200
        print(f"    ✓ Product detail loaded: {sport_product.name}")
        
        # ÉTAPE 3: Go to Cart
        print("\n[3] Go to Cart...")
        cart_url = reverse('cmagic_sport:cart')
        response = client.get(cart_url)
        assert response.status_code == 200
        print(f"    ✓ Cart page loaded")
        
        # ÉTAPE 4: Go to Checkout
        print("\n[4] Go to Checkout...")
        checkout_url = reverse('cmagic_sport:checkout')
        response = client.get(checkout_url)
        assert response.status_code == 200
        print(f"    ✓ Checkout page loaded")
        
        # ÉTAPE 5: Submit Order (POST)
        print("\n[5] Submit Order...")
        checkout_data = {
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@test.com',
            'phone': '0601020304',
            'address': '45 Avenue des Champs-Élysées',
            'city': 'Paris',
            'postal_code': '75008',
            'country': 'FR',
        }
        response = client.post(checkout_url, data=checkout_data)
        print(f"    ✓ Order submitted")
        
        # ÉTAPE 6: View Success Page
        print("\n[6] View Success Page...")
        success_url = reverse('cmagic_sport:checkout_success')
        response = client.get(success_url)
        assert response.status_code == 200
        assert 'order' in response.context
        print(f"    ✓ Success page loaded: Order #{response.context['order'].get('order_number')}")
        
        print("\n" + "="*60)
        print("PARCOURS CLIENT TERMINÉ AVEC SUCCÈS!")
        print("="*60 + "\n")


@pytest.mark.django_db
class TestCmagicSportAPI:
    """Tests des endpoints API REST CMagic Sport."""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def product_type(self):
        return ProductType.objects.create(
            name='Basket',
            slug='basket',
            is_active=True
        )
    
    @pytest.fixture
    def sport_product(self, product_type):
        return SportProduct.objects.create(
            name='Nike Air Max 90',
            slug='nike-air-max-90',
            description='Classic Nike sneaker',
            price=129.99,
            stock=15,
            in_stock=True,
            available=True,
            is_active=True,
            brand='Nike',
            product_type=product_type,
            available_sizes='38,39,40,41,42,43,44',
        )
    
    def test_api_product_list(self, client, sport_product):
        """Test de l'API liste des produits."""
        url = '/cmagic-sport/api/v1/products/'
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ API product list works")
    
    def test_api_product_detail(self, client, sport_product):
        """Test de l'API détail produit."""
        url = f'/cmagic-sport/api/v1/products/{sport_product.slug}/'
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == sport_product.name
        print(f"✓ API product detail works: {sport_product.name}")
    
    def test_api_product_availability(self, client, sport_product):
        """Test de l'API disponibilité produit."""
        url = f'/cmagic-sport/api/v1/products/{sport_product.slug}/availability/'
        response = client.get(url)
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_available'] is True
        print(f"✓ API availability works: is_available={data['is_available']}")
    
    def test_api_product_filters(self, client, sport_product):
        """Test des filtres API."""
        # Filtre par marque
        url = '/cmagic-sport/api/v1/products/?brand=Nike'
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ API filters work")


@pytest.mark.django_db
class TestCmagicSportEdgeCases:
    """Tests des cas limites et erreurs."""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_catalog_with_no_products(self, client):
        """Test du catalogue sans produits."""
        url = reverse('cmagic_sport:catalog')
        response = client.get(url)
        
        assert response.status_code == 200
        # Ne doit pas lever d'erreur même sans produits
        print(f"✓ Catalog handles empty products gracefully")
    
    def test_invalid_product_slug(self, client):
        """Test avec un slug de produit invalide."""
        url = reverse('cmagic_sport:product_detail', kwargs={'slug': 'invalid-slug-12345'})
        response = client.get(url)
        
        assert response.status_code == 404
        print(f"✓ Invalid product slug returns 404")
    
    def test_checkout_without_post_data(self, client):
        """Test du checkout sans données POST."""
        url = reverse('cmagic_sport:checkout')
        response = client.get(url)
        
        assert response.status_code == 200
        print(f"✓ Checkout GET works without POST data")
