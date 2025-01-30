from django.contrib import admin
from .models import Profile, Services, Referral, ProductScheme, Payment

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'referred_by', 'kyc_document_type', 'pan_card', 'bank_passbook')
    search_fields = ('user__username', 'referral_code')
    list_filter = ('kyc_document_type',)

class ServicesAdmin(admin.ModelAdmin):
    list_display = ('title', 'product_id', 'total')
    search_fields = ('title', 'product_id')
    list_filter = ('total',)

class ProductSchemeAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'investment', 'start_date', 'end_date', 'days', 'total', 'profile')
    search_fields = ('product_id', 'investment', 'start_date', 'end_date', 'days', 'total', 'profile__user__username')
    list_filter = ('start_date', 'end_date', 'investment')
    ordering = ('-start_date',)  # Order by start date, descending

    # Optionally, make the profile field readonly
    readonly_fields = ('profile',)

class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referred_by', 'referred_user', 'timestamp')

@admin.action(description="Approve selected payments")
def approve_payments(modeladmin, request, queryset):
    queryset.update(payment_status='approved')

@admin.action(description="Reject selected payments")
def reject_payments(modeladmin, request, queryset):
    queryset.update(payment_status='rejected')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'product_scheme', 'amount_paid', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('profile__user__username', 'product_scheme__product_id')
    actions = [approve_payments, reject_payments]

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(Services,ServicesAdmin)
admin.site.register(ProductScheme,ProductSchemeAdmin)
admin.site.register(Referral,ReferralAdmin)

