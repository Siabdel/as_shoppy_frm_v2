from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from customer.forms import CustomerUserChangeForm, CustomerCreatForm
from customer import models as acc_models

# admin.site.register(User, UserAdmin)

# Register your models here.
@admin.register(acc_models.Customer)
class AccountsAdmin(admin.ModelAdmin):
    list_display  = [f.name for f in acc_models.Customer._meta.get_fields()]
    list_display =  ('code', 'email', 'first_name', 'last_name', 'company',
                  'address1', 'address2', 'country', 'phone_number',  )
    fieldsets = (
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                )
            },
        ),
        (
            "Company Info",
            {
                "classes": ("collapse",),
                "fields": (
                    "company",
                    "company_logo",
                    "address1",
                    "address2",
                    "country",
                ),
            },
        ),
    )

class CustomerUserAdmin(UserAdmin):
    add_form = CustomerCreatForm
    form = CustomerUserChangeForm
    model = acc_models.Customer
    list_display = ["first_name", "last_name", "email", "country", ]

    fieldsets = (
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password",
                    "phone_number",
                )
            },
        ),
        (
            "Company Info",
            {
                "classes": ("collapse",),
                "fields": (
                    "company",
                    "company_logo",
                    "address1",
                    "address2",
                    "country",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("collapse",),
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
    )


## admin.site.register(Customer, CustomerUserAdmin) 