# CMagic Sport - E-Commerce Basketball Shoes Store

## Overview

This is a complete Django e-commerce solution for "CMagic Sport" - a basketball shoes online store with a professional admin interface.

## What's Included

### 1. Management Command - Load Fake Data

**File:** `product/management/commands/load_cmagic_sport_data.py`

Creates 20 basketball shoe products with:
- Real product names (Nike, Adidas, Jordan, etc.)
- Realistic descriptions and pricing
- Downloaded images from Unsplash
- Product categories

**Usage:**
```bash
python manage.py load_cmagic_sport_data
```

### 2. Responsive Templates (Bootstrap 5)

All templates use Bootstrap 5 with a modern, responsive design:

| Template | Path | Description |
|----------|------|-------------|
| Base Template | `product/templates/product/base_cmagic.html` | Main template with navbar and footer |
| Home Page | `product/templates/product/home.html` | Hero section, featured products |
| Product List | `product/templates/product/product_list_cmagic.html` | Grid layout with filters |
| Product Detail | `product/templates/product/product_detail_cmagic.html` | Full product info with tabs |
| Cart | `templates/cart/cart_detail_cmagic.html` | Shopping cart with summary |
| Checkout | `templates/shop/checkout_cmagic.html` | Multi-step checkout form |
| Dashboard | `templates/customer/dashboard_cmagic.html` | User account dashboard |

### 3. Professional Admin Interface

**File:** `product/admin_cmagic.py`
- Enhanced Product Admin with image previews
- Status badges and stock indicators
- Custom fieldsets for organization

**Custom Admin Templates:**
- `templates/admin/cmagic_sport/base.html` - CMagic-branded admin theme

## Features

### Customer Features:
- 🏀 Browse basketball shoes by category
- 🔍 Search and filter products
- 🛒 Add to cart functionality
- 💳 Checkout with payment options
- 👤 User dashboard with order history

### Admin Features:
- 📦 Product management with image upload
- 📊 Stock tracking
- 💰 Pricing management
- 📈 Order management

## Design Highlights

- **Color Scheme:** Orange (#ff6b35) primary, Dark Blue (#1a1a2e) secondary
- **Typography:** Poppins font family
- **Responsive:** Works on mobile, tablet, and desktop
- **Modern UI:** Gradient backgrounds, smooth animations, card layouts

## How to Use

### 1. Load Sample Data
```bash
python manage.py load_cmagic_sport_data
```

### 2. Run Development Server
```bash
python manage.py runserver
```

### 3. Access the Store
- Frontend: http://localhost:8000/
- Admin: http://localhost:8000/admin/

### 4. Configure URLs (in your urls.py)

The URLs are already configured in the project. The home page is accessible at:
- **Home:** http://localhost:8000/
- **Shop:** http://localhost:8000/shop/
- **Product Detail:** http://localhost:8000/product/1/
- **Cart:** http://localhost:8000/cart/
- **Admin:** http://localhost:8000/admin/

## Template Structure

```
templates/
├── admin/
│   └── cmagic_sport/
│       └── base.html          # Custom admin theme
├── cart/
│   └── cart_detail_cmagic.html  # Shopping cart
├── shop/
│   └── checkout_cmagic.html      # Checkout page
├── customer/
│   └── dashboard_cmagic.html    # User dashboard
└── product/
    └── templates/
        └── product/
            ├── base_cmagic.html        # Base template
            ├── home.html              # Homepage
            ├── product_list_cmagic.html  # Product listing
            └── product_detail_cmagic.html # Product detail
```

## Customization

### Change Logo/Brand Name
Edit in `base_cmagic.html`:
```html
<a class="navbar-brand" href="...">
    <i class="bi bi-basketball"></i> CMagic Sport
</a>
```

### Change Colors
Edit CSS variables in `base_cmagic.html`:
```css
:root {
    --cmagic-primary: #ff6b35;
    --cmagic-secondary: #1a1a2e;
}
```

## Dependencies

- Django 4.x
- Bootstrap 5.3
- Bootstrap Icons
- jQuery 3.7
- Django Crispy Forms

## Notes

- The management command will download product images from Unsplash
- Products are linked to a default Project and Societe
- Cart and checkout require the existing cart/orders apps

## License

This is a demo e-commerce project for educational purposes.
