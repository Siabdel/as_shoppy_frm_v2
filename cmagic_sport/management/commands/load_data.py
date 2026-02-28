#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Management command to load CMagic Sport fake data with images.
Usage: python manage.py load_data --app=cmagic_sport
"""
import os
import urllib.request
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from cmagic_sport.models import SportProduct
from core.taxonomy.models import MPCategory
from product.models import ProductType, ProductSpecification, ProductSpecificationValue, ProductImage


class Command(BaseCommand):
    help = 'Load CMagic Sport fake data with basketball shoes and images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing SportProducts before loading new data',
        )

    def handle(self, *args, **options):
        clear_existing = options.get('clear', False)

        if clear_existing:
            self._clear_existing_data()

        self.stdout.write(self.style.SUCCESS('Starting CMagic Sport data loading...'))

        # Create categories
        category = self._create_category()

        # Create ProductTypes and Specifications
        product_type, specs = self._create_product_types_and_specs()

        # Create basketball shoes products
        self._create_products(category, product_type, specs)

        self.stdout.write(
            self.style.SUCCESS('CMagic Sport data loaded successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created {SportProduct.objects.count()} SportProducts')
        )

    def _clear_existing_data(self):
        """Clear existing SportProducts and related data safely"""
        from django.db import connection
        from django.contrib.contenttypes.models import ContentType

        self.stdout.write(self.style.WARNING('Clearing existing SportProducts...'))

        # Get SportProduct content type
        try:
            sport_ct = ContentType.objects.get(
                app_label='cmagic_sport',
                model='sportproduct'
            )
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING('No SportProduct content type found'))
            return

        # Get SportProduct IDs
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM cmagic_sport_sportproduct")
            ids = [row[0] for row in cursor.fetchall()]

            if ids:
                ids_str = ','.join(str(i) for i in ids)

                # Delete related ProductSpecificationValue
                cursor.execute("""
                    DELETE FROM product_productspecificationvalue
                    WHERE product_object_id IN (%s)
                    AND product_content_type_id = %%s
                """ % ids_str, [sport_ct.id])

                # Delete related ProductImage
                cursor.execute("""
                    DELETE FROM product_productimage
                    WHERE product_object_id IN (%s)
                    AND product_content_type_id = %%s
                """ % ids_str, [sport_ct.id])

                # Delete SportProducts
                cursor.execute(
                    f"DELETE FROM cmagic_sport_sportproduct WHERE id IN ({ids_str})"
                )

                self.stdout.write(
                    self.style.SUCCESS(f'   Deleted {len(ids)} SportProducts and related data')
                )
            else:
                self.stdout.write(self.style.WARNING('   No existing SportProducts found'))

    def _create_category(self):
        """Create or get the Basketball category"""
        category, created = MPCategory.objects.get_or_create(
            name='Basketball',
            defaults={
                'slug': 'basketball',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('   Created category: Basketball'))
        return category

    def _create_product_types_and_specs(self):
        """Create ProductTypes and ProductSpecifications for basketball shoes"""

        # Create ProductType for Basketball Shoes
        product_type, created = ProductType.objects.get_or_create(
            name='Basketball Shoes',
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS('   Created ProductType: Basketball Shoes')
            )

        # Create specifications for basketball shoes
        specs_data = [
            {'name': 'Brand', 'product_type': product_type},
            {'name': 'Model', 'product_type': product_type},
            {'name': 'Category', 'product_type': product_type},
            {'name': 'SKU', 'product_type': product_type},
            {'name': 'Availability', 'product_type': product_type},
            {'name': 'Weight', 'product_type': product_type},
            {'name': 'Color', 'product_type': product_type},
            {'name': 'Size', 'product_type': product_type},
            {'name': 'Material', 'product_type': product_type},
            {'name': 'Sole Type', 'product_type': product_type},
            {'name': 'Cushioning', 'product_type': product_type},
            {'name': 'Closure Type', 'product_type': product_type},
            {'name': 'Gender', 'product_type': product_type},
            {'name': 'Sport Type', 'product_type': product_type},
        ]

        created_specs = {}
        for spec_data in specs_data:
            spec, created = ProductSpecification.objects.get_or_create(
                name=spec_data['name'],
                product_type=spec_data['product_type']
            )
            created_specs[spec_data['name']] = spec

        return product_type, created_specs

    def _create_products(self, category, product_type, specs):
        """Create basketball shoe SportProducts"""

        # Basketball shoes data with realistic information
        products_data = [
            {
                'name': 'Air Jordan 37 Retro',
                'description': 'The Air Jordan 37 brings back the iconic design elements of the Air Jordan 7 with modern cushioning technology.',
                'price': 189.99,
                'regular_price': 219.99,
                'stock': 50,
                'brand': 'Nike',
                'color': 'Black/White/Red',
                'size': 'US 8-13',
                'available_sizes': '38,39,40,41,42,43,44,45',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike Lebron 20',
                'description': 'Designed for LeBron James, the Nike Lebron 20 features a low-cut silhouette with maximal cushioning.',
                'price': 199.99,
                'regular_price': 249.99,
                'stock': 35,
                'brand': 'Nike',
                'color': 'White/Gold',
                'size': 'US 7-14',
                'available_sizes': '40,41,42,43,44,45,46,47',
                'collection_year': 2024,
                'is_limited_edition': True,
            },
            {
                'name': 'Adidas Dame 8',
                'description': 'The Adidas Dame 8 is built for explosive guards who need speed and control.',
                'price': 139.99,
                'regular_price': 159.99,
                'stock': 45,
                'brand': 'Adidas',
                'color': 'Core Black/White',
                'size': 'US 7-13',
                'available_sizes': '39,40,41,42,43,44,45',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Under Armour Curry 10',
                'description': 'The Curry 10 features UA Flow cushioning technology for incredible court feel.',
                'price': 179.99,
                'regular_price': 199.99,
                'stock': 40,
                'brand': 'Under Armour',
                'color': 'Blue/White',
                'size': 'US 7-15',
                'available_sizes': '40,41,42,43,44,45,46,47,48',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike KD 15',
                'description': 'The Nike KD 15 is designed for Kevin Durant\'s versatile playing style.',
                'price': 159.99,
                'regular_price': 179.99,
                'stock': 55,
                'brand': 'Nike',
                'color': 'Black/Bright Crimson',
                'size': 'US 7-14',
                'available_sizes': '40,41,42,43,44,45,46',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Jordan Zion 2',
                'description': 'The Jordan Zion 2 is built for explosive power with a large Air Zoom unit.',
                'price': 169.99,
                'regular_price': 189.99,
                'stock': 30,
                'brand': 'Jordan',
                'color': 'Navy/Orange',
                'size': 'US 8-13',
                'available_sizes': '41,42,43,44,45',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike PG 6',
                'description': 'The Nike PG 6 is designed for Paul George\'s all-around game.',
                'price': 149.99,
                'regular_price': 169.99,
                'stock': 42,
                'brand': 'Nike',
                'color': 'Blue/White',
                'size': 'US 8-13',
                'available_sizes': '40,41,42,43,44,45',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Adidas Harden Vol. 7',
                'description': 'The Adidas Harden Vol. 7 features a unique silhouette with Lightstrike cushioning.',
                'price': 189.99,
                'regular_price': 199.99,
                'stock': 38,
                'brand': 'Adidas',
                'color': 'Black/Gold',
                'size': 'US 7-14',
                'available_sizes': '40,41,42,43,44,45,46,47',
                'collection_year': 2024,
                'is_limited_edition': True,
            },
            {
                'name': 'Nike Kyrie 9',
                'description': 'The Nike Kyrie 9 is designed for explosive guards with quick changes of direction.',
                'price': 139.99,
                'regular_price': 159.99,
                'stock': 48,
                'brand': 'Nike',
                'color': 'Black/Orange',
                'size': 'US 6-13',
                'available_sizes': '38,39,40,41,42,43,44,45',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Puma MB.02',
                'description': 'The Puma MB.02 is LaMelo Ball\'s signature shoe with Nitro foam.',
                'price': 159.99,
                'regular_price': 179.99,
                'stock': 52,
                'brand': 'Puma',
                'color': 'Blue/Red',
                'size': 'US 7-13',
                'available_sizes': '40,41,42,43,44,45,46',
                'collection_year': 2024,
                'is_limited_edition': True,
            },
            {
                'name': 'Nike Air Max Impact 4',
                'description': 'The Nike Air Max Impact 4 provides great value with Air Max cushioning.',
                'price': 89.99,
                'regular_price': 109.99,
                'stock': 60,
                'brand': 'Nike',
                'color': 'White/Black',
                'size': 'US 7-14',
                'available_sizes': '40,41,42,43,44,45,46,47',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Adidas D.O.N. Issue 4',
                'description': 'The Adidas D.O.N. Issue 4 is Donovan Mitchell\'s fourth signature shoe.',
                'price': 129.99,
                'regular_price': 149.99,
                'stock': 44,
                'brand': 'Adidas',
                'color': 'Red/Black',
                'size': 'US 7-13',
                'available_sizes': '39,40,41,42,43,44,45',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike Giannis Immortality 3',
                'description': 'The Nike Giannis Immortality 3 is designed for the Greek Freak\'s powerful game.',
                'price': 119.99,
                'regular_price': 139.99,
                'stock': 36,
                'brand': 'Nike',
                'color': 'White/Greek Blue',
                'size': 'US 8-14',
                'available_sizes': '41,42,43,44,45,46,47',
                'collection_year': 2023,
                'is_limited_edition': False,
            },
            {
                'name': 'Jordan Luka 2',
                'description': 'The Jordan Luka 2 is designed for Luka Dončić\'s creative style.',
                'price': 169.99,
                'regular_price': 189.99,
                'stock': 32,
                'brand': 'Jordan',
                'color': 'White/Blue',
                'size': 'US 7-13',
                'available_sizes': '40,41,42,43,44,45,46',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike Sabrina 1',
                'description': 'The Nike Sabrina 1 is designed for women\'s basketball.',
                'price': 130.00,
                'regular_price': 150.00,
                'stock': 40,
                'brand': 'Nike',
                'color': 'Pink/White',
                'size': 'US 5-11',
                'available_sizes': '35,36,37,38,39,40,41',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike Air Jordan 1 High OG',
                'description': 'The Air Jordan 1 High OG brings back the classic silhouette with premium materials.',
                'price': 180.00,
                'regular_price': 200.00,
                'stock': 28,
                'brand': 'Nike',
                'color': 'Chicago/White',
                'size': 'US 7-13',
                'available_sizes': '40,41,42,43,44,45,46',
                'collection_year': 2024,
                'is_limited_edition': True,
            },
            {
                'name': 'Under Armour Flow 2.0',
                'description': 'The Under Armour Flow 2.0 features UA Flow cushioning for incredible court feel.',
                'price': 149.99,
                'regular_price': 169.99,
                'stock': 46,
                'brand': 'Under Armour',
                'color': 'Black/White',
                'size': 'US 7-14',
                'available_sizes': '40,41,42,43,44,45,46,47',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike LeBron NXXT Gen',
                'description': 'The Nike LeBron NXXT Gen is the latest in LeBron\'s line with low-cut design.',
                'price': 210.00,
                'regular_price': 240.00,
                'stock': 25,
                'brand': 'Nike',
                'color': 'White/Neon',
                'size': 'US 7-15',
                'available_sizes': '40,41,42,43,44,45,46,47,48',
                'collection_year': 2024,
                'is_limited_edition': True,
            },
            {
                'name': 'Adidas Trae Young 2',
                'description': 'The Adidas Trae Young 2 is designed for the young star with excellent court feel.',
                'price': 175.00,
                'regular_price': 195.00,
                'stock': 34,
                'brand': 'Adidas',
                'color': 'White/Red',
                'size': 'US 7-13',
                'available_sizes': '40,41,42,43,44,45,46',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
            {
                'name': 'Nike Zoom Freak 4',
                'description': 'The Nike Zoom Freak 4 is Giannis Antetokounmpo\'s fourth signature shoe.',
                'price': 145.00,
                'regular_price': 165.00,
                'stock': 42,
                'brand': 'Nike',
                'color': 'White/Blue/Red',
                'size': 'US 8-14',
                'available_sizes': '41,42,43,44,45,46,47',
                'collection_year': 2024,
                'is_limited_edition': False,
            },
        ]

        # Image URLs for basketball shoes
        image_urls = [
            'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1539185441755-769473a23570?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1551107696-a4b0c5a0d9a2?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1579338559194-a162d19bf842?w=400&h=400&fit=crop',
            'https://images.unsplash.com/photo-1584735175315-9d5df23860e6?w=400&h=400&fit=crop',
        ]

        # Create products
        for i, product_data in enumerate(products_data):
            # Generate unique slug
            base_slug = slugify(product_data['name'])
            slug = f"{base_slug}-{i+1}"

            # Check if product already exists
            if SportProduct.objects.filter(slug=slug).exists():
                self.stdout.write(
                    self.style.WARNING(f'   Product already exists: {product_data["name"]}')
                )
                continue

            # Create SportProduct
            product = SportProduct.objects.create(
                name=product_data['name'],
                slug=slug,
                description=product_data['description'],
                price=product_data['price'],
                regular_price=product_data['regular_price'],
                stock=product_data['stock'],
                category=category,
                product_type=product_type,
                available=True,
                in_stock=True,
                is_active=True,
                # SportProduct specific fields
                available_sizes=product_data['available_sizes'],
                collection_year=product_data['collection_year'],
                is_limited_edition=product_data['is_limited_edition'],
            )

            # Create specification values for this product
            self._create_product_spec_values(product, product_data, specs)

            # Download and assign image
            image_url = image_urls[i % len(image_urls)]
            self._download_and_assign_image(product, image_url, i)

            self.stdout.write(
                self.style.SUCCESS(
                    f'   Created SportProduct: {product.name} - ${product.price}'
                )
            )

    def _create_product_spec_values(self, product, product_data, specs):
        """Create ProductSpecificationValue for a product"""

        # Map specification values based on product data
        spec_values_map = {
            'Brand': product_data.get('brand', 'N/A'),
            'Model': product_data.get('name', ''),
            'Category': 'Basketball Shoes',
            'SKU': f'CMAGIC-{product.pk:06d}',
            'Availability': 'In Stock' if product.stock > 0 else 'Out of Stock',
            'Weight': '0.5 kg',
            'Color': product_data.get('color', 'N/A'),
            'Size': product_data.get('size', 'N/A'),
            'Material': 'Synthetic/Leather',
            'Sole Type': 'Rubber',
            'Cushioning': 'Zoom Air / React',
            'Closure Type': 'Lace-up',
            'Gender': 'Unisex',
            'Sport Type': 'Basketball',
        }

        # Create specification values
        for spec_name, spec in specs.items():
            value = spec_values_map.get(spec_name, 'N/A')
            ProductSpecificationValue.objects.create(
                product=product,
                specification=spec,
                value=str(value)
            )

    def _download_and_assign_image(self, product, image_url, index):
        """Download image from URL and assign to product"""
        try:
            # Create media directory if needed
            media_root = 'static/product_images/cmagic_sport'
            os.makedirs(media_root, exist_ok=True)

            # Generate filename
            filename = f"{product.slug}_{index+1}.jpg"
            filepath = os.path.join(media_root, filename)

            # Download image
            urllib.request.urlretrieve(image_url, filepath)

            # Create ProductImage
            ProductImage.objects.create(
                product=product,
                image=f"product_images/cmagic_sport/{filename}",
                title=f"{product.name} - Image {index + 1}",
            )

            self.stdout.write(self.style.SUCCESS(f'   Downloaded image for {product.name}'))

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'   Could not download image for {product.name}: {e}')
            )
