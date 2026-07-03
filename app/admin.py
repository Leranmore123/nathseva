from django.contrib import admin
from .models import Retailer, PaymentRequest, PANApplication, WalletTransaction


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
	list_display = ('user_id', 'full_name', 'mobile', 'wallet_balance', 'is_verified', 'is_active')
	search_fields = ('user_id', 'full_name', 'mobile')


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
	list_display = ('retailer', 'amount', 'status', 'created_at')
	list_filter = ('status',)


@admin.register(PANApplication)
class PANApplicationAdmin(admin.ModelAdmin):
	list_display = ('order_id', 'full_name', 'pan_number', 'status', 'created_at')
	search_fields = ('order_id', 'full_name', 'pan_number')


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
	list_display = ('retailer', 'tx_type', 'amount', 'status', 'payment_provider', 'provider_order_id', 'provider_payment_id', 'created_at')
	list_filter = ('status', 'tx_type', 'payment_provider')
	search_fields = ('retailer__user_id', 'provider_order_id', 'provider_payment_id')
