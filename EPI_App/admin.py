from decimal import Decimal
from django.contrib import admin
from .models import Investment, Profile, Services, Referral, ProductScheme, Payment

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'referral_code', 'referred_by', 'profile_photo', 'kyc_document_type', 'pan_card', 'bank_passbook', 'referrals_made', 'rewards_earned')
    search_fields = ('user_username', 'referral_code', 'referred_by_username')  # Use double underscore for related fields
    list_filter = ('kyc_document_type', 'referred_by')
    readonly_fields = ('referral_code', 'referrals_made', 'rewards_earned')  # Prevent editing of these fields

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'referral_code', 'referred_by', 'profile_photo'),  # Include profile_photo here
        }),
        ('KYC Details', {
            'fields': ('kyc_document_type', 'kyc_document', 'pan_card', 'bank_passbook'),
        }),
        ('Referral Information', {
            'fields': ['referrals_made', 'rewards_earned'],
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # Make referral_code and referred_by read-only after creation
        if obj:  # Editing an existing object
            return self.readonly_fields + ('referral_code', 'referred_by')
        return self.readonly_fields

    # Add an action to manually add rewards (if needed)
    @admin.action(description="Add reward to selected users")
    def add_rewards_to_selected(self, request, queryset):
        for profile in queryset:
            profile.add_rewards(Decimal('10.00'))  # Add a fixed reward amount
            self.message_user(request, f"Rewards added to {profile.user.username}'s profile.")

admin.site.register(Profile, ProfileAdmin)

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
    search_fields = ('referred_by__userusername', 'referred_user__username')
    list_filter = ('timestamp', 'referred_by__user__username')
    readonly_fields = ('timestamp',)  # Prevent editing of the timestamp

    def get_readonly_fields(self, request, obj=None):
        # Make referred_by and referred_user read-only after creation
        if obj:  # Editing an existing object
            return self.readonly_fields + ('referred_by', 'referred_user')
        return self.readonly_fields

admin.site.register(Referral, ReferralAdmin)

@admin.action(description="Approve selected payments")
def approve_payments(modeladmin, request, queryset):
    queryset.update(payment_status='approved')

@admin.action(description="Reject selected payments")
def reject_payments(modeladmin, request, queryset):
    queryset.update(payment_status='rejected')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'product_scheme', 'transaction_id', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('profile__user__username', 'product_scheme__product_id')
    actions = [approve_payments, reject_payments]

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('product', 'referred_user', 'daily_investment', 'total_amount', 'days_to_complete')
    
    def product(self, obj):
        return obj.product.title if obj.product else "Unknown"

admin.site.register(Investment, InvestmentAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Services,ServicesAdmin)
admin.site.register(ProductScheme,ProductSchemeAdmin)

