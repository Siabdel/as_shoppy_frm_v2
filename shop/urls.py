from django.urls import path
from shop import views

app_name = "shop"

urlpatterns = [
    #path('cat/<slug:category_slug>/', views.product_shop_list, name='product_list_by_category'),
    path('list/<int:project_id>/', views.product_shop_list, name='product_shop_list'),
    path('show/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('show/<str:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('add/<int:product_id>/', views.cart_add_one_item, name='cart_add_item'),
    path('s_cart/', views.cart_summary, name='cart_summary'),
    path('s_client/', views.ClientCheck.as_view(), name='client_checkout'),
    # Checkout workflow
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
]