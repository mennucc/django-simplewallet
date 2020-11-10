from django.contrib import admin

# Register your models here.

# https://docs.djangoproject.com/en/3.0/ref/contrib/admin/

from .models import BuyableObject

admin.site.register(BuyableObject)
