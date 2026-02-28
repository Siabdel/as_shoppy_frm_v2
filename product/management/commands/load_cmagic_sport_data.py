#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Management command to load CMagic Sport fake data with images.
Usage: python manage.py load_cmagic_sport_data
"""
import os
import random
import urllib.request
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from core.taxonomy.models import MPCategory
from product.models import Product, ProductImage, ProductType, ProductSpecification, ProductSpecificationValue
from cmagic_sport.models import SportProduct
from project.models import Project
from core.profile.models import Societe


class Command(BaseCommand):
    help = 'Load CMagic Sport fake data with basketball shoes and images'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting CMagic Sport data loading...'))
        
        # Get existing project or create new one
        project = None
        try:
            project = Project.objects.first()
            if project:
                self.stdout.write(self.style.SUCCESS('Using existing project'))
            else:
                # Try to create a new project
                societe = self._get_or_create_societe()
                project = self._create_project_safe(societe)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Project error: {e}'))
            # Try to find any project
            try:
                project = Project.objects.first()
            except:
                pass
        
        # Create categories
        categories = self._create_categories()
        
        # Create ProductTypes and Specifications
        product_type, specs = self._create_product_types_and_specs()
        
        # Create basketball shoes products
        self._create_products(project, categories, product_type, specs)
        
        self.stdout.write(self.style.SUCCESS('CMagic Sport data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Created {Product.objects.count()} products'))

    def _get_or_create_societe(self):
        """Create or get the company"""
        societe, created = Societe.objects.get_or_create(
            name='CMagic Sport',
            defaults={
                'description': 'Basketball shoes e-commerce store',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('   🏢 Created company: CMagic Sport'))
        return societe

    def _create_project_safe(self, societe):
        """Create project safely avoiding double-save issues"""
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            # Try to get existing first
            project = Project.objects.filter(societe=societe).first()
            if project:
                return project
            
            # Create with explicit code to avoid auto-generation issues
            project = Project(
                name='CMagic Sport E-Commerce',
                societe=societe,
                start_date=timezone.now(),
                due_date=timezone.now() + timedelta(days=365),
            )
            # Set code directly to avoid auto-generation
            project.code = f'CMAGIC-{timezone.now().strftime("%Y%m%d")}'
            project.save(force_insert=True)
            self.stdout.write(self.style.SUCCESS('   🛒 Created project: CMagic Sport E-Commerce'))
            return project
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   Could not create project: {e}'))
            # Try to get any existing project
            return Project.objects.first()

    def _create_categories(self):
        """Get existing or create minimal categories"""
        # Use existing categories or create simple ones
        categories = {}
        
        # Try to get existing
        existing = MPCategory.objects.all()[:4]
        if existing:
            for cat in existing:
                categories[cat.name] = cat
                self.stdout.write(f'   Using category: {cat.name}')
        else:
            # Create basic category
            cat, _ = MPCategory.objects.get_or_create(name='Basketball')
            categories['Basketball'] = cat
            self.stdout.write(self.style.SUCCESS(f'   Created category: Basketball'))
        
        return categories

    def _create_product_types_and_specs(self):
        """Create ProductTypes and ProductSpecifications for basketball shoes"""
        
        # Create ProductType for Basketball Shoes
        product_type, created = ProductType.objects.get_or_create(
            name='Basketball Shoes',
            defaults={'is_active': True}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'   Created ProductType: Basketball Shoes'))
        
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

    def _create_products(self, project, categories, product_type=None, specs=None):
        """Create basketball shoe products - ensure valid project"""
        
        # Ensure we have a valid project - this is required for Product model
        if not project:
            # Try to get any existing project
            project = Project.objects.first()
            if not project:
                # Create minimal project if none exists
                societe = self._get_or_create_societe()
                project = self._create_project_safe(societe)
        
        if not project:
            self.stdout.write(self.style.ERROR('No project available - cannot create products'))
            return
        
        # Use first available category
        cat = list(categories.values())[0] if categories else None
        
        # Basketball shoes data with realistic information
        products_data = [
            {
                'name': 'Air Jordan 37 Retro',
                'description': 'The Air Jordan 37 brings back the iconic design elements of the Air Jordan 7 with modern cushioning technology. Features include a full-length Zoom Air unit and React foam for explosive energy return.',
                'price': 189.99,
                'regular_price': 219.99,
                'stock': 50,
                'category': 'Basketball Shoes',
                'brand': 'Nike',
                'color': 'Black/White/Red',
                'size': 'US 8-13',
            },
            {
                'name': 'Nike Lebron 20',
                'description': 'Designed for LeBron James, the Nike Lebron 20 features a low-cut silhouette with maximal cushioning. Includes a full-length Zoom Air unit and a carbon fiber plate for stability and propulsion.',
                'price': 199.99,
                'regular_price': 249.99,
                'stock': 35,
                'category': 'Basketball Shoes',
                'brand': 'Nike',
                'color': 'White/Gold',
                'size': 'US 7-14',
            },
            {
                'name': 'Adidas Dame 8',
                'description': 'The Adidas Dame 8 is built for explosive guards who need speed and control. Features Bounce cushioning and a lightweight mesh upper for breathability.',
                'price': 139.99,
                'regular_price': 159.99,
                'stock': 45,
                'category': 'Men\'s Basketball',
                'brand': 'Adidas',
                'color': 'Core Black/White',
                'size': 'US 7-13',
            },
            {
                'name': 'Under Armour Curry 10',
                'description': 'The Curry 10 features UA Flow cushioning technology for incredible court feel. Designed for Stephen Curry fans who want premium performance.',
                'price': 179.99,
                'regular_price': 199.99,
                'stock': 40,
                'category': 'Basketball Shoes',
                'brand': 'Under Armour',
                'color': 'Blue/White',
                'size': 'US 7-15',
            },
            {
                'name': 'Nike KD 15',
                'description': 'The Nike KD 15 is designed for Kevin Durant\'s versatile playing style. Features a full-length Zoom Air Strobel unit for responsive cushioning.',
                'price': 159.99,
                'regular_price': 179.99,
                'stock': 55,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'Black/Bright Crimson',
                'size': 'US 7-14',
            },
            {
                'name': 'Jordan Zion 2',
                'description': 'The Jordan Zion 2 is built for explosive power. Features a large Air Zoom unit in the forefoot and a padded collar for ankle support.',
                'price': 169.99,
                'regular_price': 189.99,
                'stock': 30,
                'category': 'Basketball Shoes',
                'brand': 'Jordan',
                'color': 'Navy/Orange',
                'size': 'US 8-13',
            },
            {
                'name': 'Nike PG 6',
                'description': 'The Nike PG 6 is designed for Paul George\'s all-around game. Features React foam for soft, responsive cushioning.',
                'price': 149.99,
                'regular_price': 169.99,
                'stock': 42,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'White/Blue',
                'size': 'US 7-13',
            },
            {
                'name': 'Adidas Harden Vol. 7',
                'description': 'The Adidas Harden Vol. 7 features a unique silhouette with a wide base for stability. Includes full-length Lightstrike cushioning.',
                'price': 189.99,
                'regular_price': 210.00,
                'stock': 28,
                'category': 'Basketball Shoes',
                'brand': 'Adidas',
                'color': 'Black/Gold',
                'size': 'US 7-14',
            },
            {
                'name': 'Nike Kyrie 9',
                'description': 'The Nike Kyrie 9 is designed for explosive guards with quick changes of direction. Features a curved outsole for smooth transitions.',
                'price': 139.99,
                'regular_price': 159.99,
                'stock': 60,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'Black/Volt',
                'size': 'US 6-14',
            },
            {
                'name': 'Puma MB.02',
                'description': 'The Puma MB.02 is LaMelo Ball\'s signature shoe. Features Nitro foam for exceptional cushioning and a unique design.',
                'price': 159.99,
                'regular_price': 175.00,
                'stock': 38,
                'category': 'Basketball Shoes',
                'brand': 'Puma',
                'color': 'Blue/Pink',
                'size': 'US 7-13',
            },
            {
                'name': 'Nike Air Max Impact 4',
                'description': 'The Nike Air Max Impact 4 provides great value with Air Max cushioning. Perfect for players who need reliable performance.',
                'price': 89.99,
                'regular_price': 110.00,
                'stock': 75,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'White/Black',
                'size': 'US 7-14',
            },
            {
                'name': 'Adidas D.O.N. Issue 4',
                'description': 'The Adidas D.O.N. Issue 4 is Donovan Mitchell\'s fourth signature shoe. Features Bounce cushioning and a grippy outsole.',
                'price': 129.99,
                'regular_price': 150.00,
                'stock': 52,
                'category': 'Basketball Shoes',
                'brand': 'Adidas',
                'color': 'Red/Black',
                'size': 'US 7-13',
            },
            {
                'name': 'Nike Giannis Immortality 3',
                'description': 'The Nike Giannis Immortality 3 is designed for the Greek Freak\'s powerful game. Features a large Air Zoom unit.',
                'price': 119.99,
                'regular_price': 140.00,
                'stock': 48,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'White/Blue',
                'size': 'US 8-15',
            },
            {
                'name': 'Jordan Luka 2',
                'description': 'The Jordan Luka 2 is designed for Luka Dončić\'s creative style. Features a full-length Formula 23 foam.',
                'price': 169.99,
                'regular_price': 195.00,
                'stock': 32,
                'category': 'Basketball Shoes',
                'brand': 'Jordan',
                'color': 'White/Green',
                'size': 'US 7-14',
            },
            {
                'name': 'Nike Sabrina 1',
                'description': 'The Nike Sabrina 1 is designed for women\'s basketball. Features a unique saddle design and responsive cushioning.',
                'price': 130.00,
                'regular_price': 150.00,
                'stock': 40,
                'category': 'Women\'s Basketball',
                'brand': 'Nike',
                'color': 'Pink/White',
                'size': 'US 5-11',
            },
            {
                'name': 'Nike Air Jordan 1 High OG',
                'description': 'The Air Jordan 1 High OG brings back the classic silhouette with premium materials. A timeless basketball shoe.',
                'price': 180.00,
                'regular_price': 200.00,
                'stock': 25,
                'category': 'Basketball Shoes',
                'brand': 'Jordan',
                'color': 'Chicago Red/White/Black',
                'size': 'US 7-13',
            },
            {
                'name': 'Under Armour Flow 2.0',
                'description': 'The Under Armour Flow 2.0 features UA Flow cushioning for incredible court feel. Lightweight and responsive.',
                'price': 149.99,
                'regular_price': 170.00,
                'stock': 45,
                'category': 'Basketball Shoes',
                'brand': 'Under Armour',
                'color': 'Black/White',
                'size': 'US 7-14',
            },
            {
                'name': 'Nike LeBron NXXT Gen',
                'description': 'The Nike LeBron NXXT Gen is the latest in LeBron\'s line. Features a low-cut design with maximal cushioning.',
                'price': 210.00,
                'regular_price': 240.00,
                'stock': 20,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'White/Black/Gold',
                'size': 'US 7-15',
            },
            {
                'name': 'Adidas Trae Young 2',
                'description': 'The Adidas Trae Young 2 is designed for the young star. Features a unique design with excellent court feel.',
                'price': 175.00,
                'regular_price': 195.00,
                'stock': 35,
                'category': 'Basketball Shoes',
                'brand': 'Adidas',
                'color': 'Red/White',
                'size': 'US 7-14',
            },
            {
                'name': 'Nike Zoom Freak 4',
                'description': 'The Nike Zoom Freak 4 is Giannis Antetokounmpo\'s fourth signature shoe. Features double Zoom Air units.',
                'price': 145.00,
                'regular_price': 165.00,
                'stock': 42,
                'category': 'Men\'s Basketball',
                'brand': 'Nike',
                'color': 'White/Blue/Red',
                'size': 'US 8-14',
            },
        ]

        # Image URLs for basketball shoes (using placeholder images)
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
            category = categories.get(product_data['category'])
            
            # Generate unique slug
            base_slug = slugify(product_data['name'])
            slug = f"{base_slug}-{i+1}"
            
            # Check if product already exists
            if Product.objects.filter(slug=slug).exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  Product already exists: {product_data["name"]}'))
                continue
            
            # Create product
            product = Product.objects.create(
                project=project,
                name=product_data['name'],
                slug=slug,
                description=product_data['description'],
                price=product_data['price'],
                regular_price=product_data['regular_price'],
                stock=product_data['stock'],
                category=category,
                available=True,
                in_stock=True,
                is_active=True,
            )
            
            # Create specification values for this product
            if specs and product_type:
                self._create_product_spec_values(product, product_data, specs, cat)
            
            # Download and assign image
            image_url = image_urls[i % len(image_urls)]
            self._download_and_assign_image(product, image_url, i)
            
            self.stdout.write(self.style.SUCCESS(f'   👟 Created product: {product.name} - ${product.price}'))

    def _create_product_spec_values(self, product, product_data, specs, category):
        """Create ProductSpecificationValue for a product"""
        
        # Map specification values based on product data
        spec_values_map = {
            'Brand': product_data.get('brand', 'N/A'),
            'Model': product_data.get('name', ''),
            'Category': product_data.get('category', 'Basketball Shoes'),
            'SKU': f'CMAGIC-{product.pk:06d}',
            'Availability': 'In Stock' if product.stock > 0 else 'Out of Stock',
            'Weight': '0.5 kg',
            'Color': product_data.get('color', 'N/A'),
            'Size': product_data.get('size', 'N/A'),
            'Material': 'Synthetic/Leather',
            'Sole Type': 'Rubber',
            'Cushioning': 'Zoom Air / React',
            'Closure Type': 'Lace-up',
            'Gender': 'Unisex' if 'Women' not in product_data.get('category', '') else 'Women',
            'Sport Type': 'Basketball',
        }
        
        for spec_name, value in spec_values_map.items():
            if spec_name in specs:
                try:
                    ProductSpecificationValue.objects.create(
                        product=product,
                        category=category,
                        specification=specs[spec_name],
                        value=value
                    )
                except Exception as e:
                    pass  # Skip if spec creation fails

    def _download_and_assign_image(self, product, image_url, index):
        """Download image from URL and assign to product"""
        try:
            # Create media directory if it doesn't exist
            media_root = settings.MEDIA_ROOT
            product_images_dir = os.path.join(media_root, 'upload', 'product_images', '2024', '02')
            os.makedirs(product_images_dir, exist_ok=True)
            
            # Generate filename
            filename = f'cmagic_shoe_{index+1}.jpg'
            filepath = os.path.join(product_images_dir, filename)
            
            # Download image
            try:
                urllib.request.urlretrieve(image_url, filepath)
                
                # Assign to product
                product.default_image = f'upload/product_images/2024/02/{filename}'
                product.save()
                
                self.stdout.write(self.style.SUCCESS(f'      🖼️  Downloaded image for {product.name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'      ⚠️  Could not download image: {str(e)[:50]}'))
                # Create a placeholder image reference
                product.default_image = 'img/default.jpg'
                product.save()
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'      ⚠️  Error assigning image: {str(e)[:50]}'))