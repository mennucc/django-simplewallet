from django.contrib import admin

# Register your models here.

# https://docs.djangoproject.com/en/3.0/ref/contrib/admin/

from .models import Transaction, Wallet


class TransactionAdmin(admin.TabularInline):
    model = Transaction

class WalletAdmin(admin.ModelAdmin):
    model = Wallet
    inlines = [
        TransactionAdmin,
    ]
    readonly_fields = ('user',)

admin.site.register(Wallet, WalletAdmin)
