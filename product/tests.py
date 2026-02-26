from django.test import TestCase
import pytest
from django.urls import reverse
from product.models import Product, ProductImage, ProductSpecificationValue
from core.taxonomy.models import MPCategory
from django.urls import reverse

@pytest.mark.django_db
def test_product_detail_view(client):
    category = MPCategory.objects.create(name="Category 1")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=10.00,
        regular_price=12.00,
        discount_price=8.00,
        available=True,
        stock=100,
        category=category,
    )
    url = reverse('product:product_detail', args=[product.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Test Product" in response.content.decode()
    
# Create your tests here.
@pytest.mark.django_db
def test_create_product():
    category = MPCategory.objects.create(name="Category 1")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=10.00,
        regular_price=12.00,
        discount_price=8.00,
        available=True,
        stock=100,
        category=category,
    )
    assert product.name == "Test Product"
    assert product.slug == "test-product"
    assert product.price == 10.00
    assert product.regular_price == 12.00
    assert product.discount_price == 8.00
    assert product.available is True
    assert product.stock == 100

@pytest.mark.django_db
def test_product_image():
    category = MPCategory.objects.create(name="Category 1")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=10.00,
        regular_price=12.00,
        discount_price=8.00,
        available=True,
        stock=100,
        category=category,
    )
    product_image = ProductImage.objects.create(
        product=product,
        title="Test Image",
        slug="test-image",
        image="path/to/image.jpg"
    )
    assert product_image.product == product
    assert product_image.title == "Test Image"

@pytest.mark.django_db
def test_product_specification_value():
    category = MPCategory.objects.create(name="Category 1")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=10.00,
        regular_price=12.00,
        discount_price=8.00,
        available=True,
        stock=100,
        category=category,
    )
    specification = ProductSpecification.objects.create(
        product_type="Test Type",
        name="Test Specification"
    )
    spec_value = ProductSpecificationValue.objects.create(
        product=product,
        specification=specification,
        value="Test Value"
    )
    assert spec_value.product == product
    assert spec_value.specification == specification
    assert spec_value.value == "Test Value"



@pytest.mark.django_db
def test_product_detail_view(client):
    category = MPCategory.objects.create(name="Category 1")
    product = Product.objects.create(
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=10.00,
        regular_price=12.00,
        discount_price=8.00,
        available=True,
        stock=100,
        category=category,
    )
    url = reverse('product:product_detail', args=[product.id])
    response = client.get(url)
    assert response.status_code == 200
    assert "Test Product" in response.content.decode()
