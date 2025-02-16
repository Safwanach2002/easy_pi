from django.db import models
from django.contrib.auth.models import User
import string
import random
from django.utils.timezone import now
from datetime import timedelta, timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    referral_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='referrals')
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    kyc_document = models.FileField(upload_to='kyc_documents/', blank=True, null=True)
    kyc_document_type = models.CharField(max_length=50, blank=True, null=True)
    pan_card = models.FileField(upload_to='pan_cards/', blank=True, null=True)
    bank_passbook = models.FileField(upload_to='bank_passbooks/', blank=True, null=True)
    referrals_made = models.IntegerField(default=0)
    rewards_earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def save(self, *args, **kwargs):
        """Automatically generate a unique referral code if not already set."""
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def generate_referral_code(self):
        """Generate a unique 8-character referral code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Profile.objects.filter(referral_code=code).exists():
                return code

    def add_referral(self, referred_user):
        """Add a referral, update the referral count, and rewards."""
        if self.user == referred_user:
            raise ValidationError("You cannot refer yourself.")
        
        if referred_user.profile.referred_by:  # Check if the referred user already has a referrer
            raise ValidationError("This user has already been referred by someone else.")

        # Create a referral entry
        Referral.objects.create(referred_by=self, referred_user=referred_user)

        # Increment the referral count
        self.referrals_made += 1
        self.save()

        # Calculate and add dynamic rewards based on the referred user's activity (e.g., daily investment)
        daily_commission = self.calculate_daily_commission(referred_user)
        self.add_rewards(daily_commission)

    def calculate_daily_commission(self, referred_user):
        """Calculate the daily commission based on the referred user's investments."""
        today = timezone.now().date()
        referred_user_investment = referred_user.investment_set.filter(date__date=today).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        # Example commission calculation: 25% of the referred user's total investment for the day
        daily_commission = referred_user_investment * Decimal('0.25')
        return daily_commission

    def add_rewards(self, amount):
        """Add rewards to the user's profile."""
        self.rewards_earned += amount
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Referral(models.Model):
    referred_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='referral_by')
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referred_user')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Referral by {self.referred_by.user.username} to {self.referred_user.username}"

    def save(self, *args, **kwargs):
        # Ensure the referred user is not the same as the referrer
        if self.referred_by.user == self.referred_user:
            raise ValidationError("You cannot refer yourself.")
        super().save(*args, **kwargs)


class Services(models.Model):
    ELECTRONICS = 'electronics'
    MOBILES = 'mobiles'
    HOME_KITCHEN = 'home_kitchen'
    FASHION = 'fashion'
    BOOKS = 'books'
    OTHERS = 'others'

    CATEGORY_CHOICES = [
        (ELECTRONICS, 'Electronics'),
        (MOBILES, 'Mobiles'),
        (HOME_KITCHEN, 'Home & Kitchen'),
        (FASHION, 'Fashion'),
        (BOOKS, 'Books'),
        (OTHERS, 'Others'),
    ]

    product_id = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    img = models.ImageField(upload_to="pics")
    desc = models.CharField(max_length=500, null=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=OTHERS,  # Default to 'Others' if no category is selected
    )

    def _str_(self):
        return self.title

class Combo(models.Model):
    ELECTRONICS = 'electronics'
    MOBILES = 'mobiles'
    HOME_KITCHEN = 'home_kitchen'
    FASHION = 'fashion'
    BOOKS = 'books'
    OTHERS = 'others'

    CATEGORY_CHOICES = [
        (ELECTRONICS, 'Electronics'),
        (MOBILES, 'Mobiles'),
        (HOME_KITCHEN, 'Home & Kitchen'),
        (FASHION, 'Fashion'),
        (BOOKS, 'Books'),
        (OTHERS, 'Others'),
    ]

    product_id = models.CharField(max_length=100, null=True)
    title = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    img = models.ImageField(upload_to="pics")
    desc = models.CharField(max_length=500, null=True)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=OTHERS,  # Default to 'Others' if no category is selected
    )

    def _str_(self):
        return self.title

class ProductScheme(models.Model):
    product_id = models.CharField(max_length=100, null=True)
    investment = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(auto_now_add=True)  # Automatically set to today's date when created
    end_date = models.DateField(null=True, blank=True)
    days = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Scheme for {self.product_id} - {self.investment} Investment"

    def calculate_end_date(self):
        """Calculate end date based on the start date and number of days."""
        return self.start_date + timedelta(days=self.days)

    def save(self, *args, **kwargs):
        """Override save method to calculate end date before saving the model."""
        if not self.end_date:
            self.end_date = self.calculate_end_date()
        super().save(*args, **kwargs)

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    product_scheme = models.ForeignKey(ProductScheme, on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=now)

    def _str_(self):
        return f"Payment for {self.product_scheme.product_id} by {self.profile.user.username}"

class Investment(models.Model):
    product = models.ForeignKey(Services, on_delete=models.CASCADE)
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE)
    daily_investment = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    days_to_complete = models.IntegerField()
    start_date = models.DateField(auto_now_add=True)
    timestamp = models.DateTimeField(default=now)

    @property
    def commission(self):
        """Calculate daily commission as 25% of the total amount, divided by the days to complete."""
        total_commission = self.total_amount * Decimal('0.25')  # 25% commission on total amount
        daily_commission = total_commission / self.days_to_complete  # Daily commission based on the number of days
        return daily_commission

    def save(self, *args, **kwargs):
        """Override save method to distribute commission to the referrer daily."""
        is_new = self.pk is None  # Check if this is a new investment

        super().save(*args, **kwargs)  # Save the investment record first

        if is_new:  # Only distribute rewards when a new investment is created
            referred_profile = self.referred_user.profile
            if referred_profile.referred_by:  # Check if there is a referrer
                referrer_profile = referred_profile.referred_by

                # Calculate daily commission (25% of total investment divided by days)
                total_commission = self.total_amount * Decimal('0.25')
                daily_commission = total_commission / self.days_to_complete

                # Add the daily commission to the referrer's rewards earned
                referrer_profile.rewards_earned += daily_commission
                referrer_profile.save()

    def __str__(self):
        return f"{self.referred_user.username}'s investment"

class PaymentOrder(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    order_id = models.CharField(max_length=100, unique=True)
    product_id = models.CharField(max_length=100, null=True)
    amount = models.IntegerField()  # Amount in paise
    currency = models.CharField(max_length=3, default='INR')
    payment_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(
        max_length=20, 
        choices=[
            ('PENDING', 'Pending'),
            ('SUCCESSFUL', 'Successful'),
            ('FAILED', 'Failed')
        ],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id} - {self.payment_status}"