from django.shortcuts import render, redirect, get_object_or_404
from .forms import SignupForm, ProductSchemeForm, PaymentForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
import random
import string
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Investment, Payment, Referral, Profile, ProductScheme, Services
from datetime import datetime, timedelta, date
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from django.db.models import Sum
from django.utils.timezone import now


# Create your views here.
def generate_referral_code():
    """Generate a unique 8-character referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            referral_code = generate_referral_code()
            referred_by_code = request.POST.get('referred_by')
            referred_by_profile = Profile.objects.filter(referral_code=referred_by_code).first()
            
            profile = Profile.objects.create(
                user=user,
                referral_code=referral_code,
                referred_by=referred_by_profile,
                kyc_document=form.cleaned_data.get('kyc_document'),
                kyc_document_type=form.cleaned_data.get('kyc_document_type'),
                pan_card=form.cleaned_data.get('pan_card'),
                bank_passbook=form.cleaned_data.get('bank_passbook'),
            )
            
            if referred_by_profile:
                referred_by_profile.referrals_made += 1
                referred_by_profile.rewards_earned += Decimal('10.00')
                referred_by_profile.save()
                Referral.objects.create(referred_by=referred_by_profile, referred_user=user)
            
            auth_login(request, user)
            return JsonResponse({'success': True, 'referral_code': referral_code, 'message': 'Signup successful! Welcome aboard!'})
        
        errors = {field: error_list for field, error_list in form.errors.get_json_data().items()}
        return JsonResponse({'success': False, 'errors': errors, 'message': 'Please correct the errors below.'})
    
    return render(request, 'signup.html', {'form': SignupForm()})

@login_required
def referral_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    referred_users = Profile.objects.filter(referred_by=profile)
    referred_investments = Investment.objects.filter(referred_user=request.user).select_related('product')
    
    total_rewards = sum((inv.daily_investment or Decimal('0')) * Decimal('0.25') * max((now().date() - inv.start_date).days, 0) for inv in referred_investments)
    
    referred_data = [{
        "name": inv.referred_user.get_full_name() or inv.referred_user.username,
        "product": inv.product.title if inv.product else "Unknown",
        "daily_investment": inv.daily_investment or Decimal('0'),
        "commission": (inv.daily_investment or Decimal('0')) * Decimal('0.25') * max((now().date() - inv.start_date).days, 0),
        "timestamp": inv.timestamp,
    } for inv in referred_investments]
    
    return render(request, 'reference.html', {
        'referral_code': profile.referral_code,
        'referrals_made': profile.referrals_made,
        'total_rewards': total_rewards,
        'referred_investments': referred_data
    })

@csrf_exempt
def submit_referral(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            referral_code = data.get('referral_code')
            
            if not referral_code:
                return JsonResponse({'success': False, 'message': 'Referral code is required.'})
            
            referred_by_profile = Profile.objects.filter(referral_code=referral_code).first()
            if not referred_by_profile:
                return JsonResponse({'success': False, 'message': 'Invalid referral code.'})
            
            user_profile = request.user.profile
            if user_profile == referred_by_profile:
                return JsonResponse({'success': False, 'message': 'You cannot refer yourself.'})
            
            user_profile.referred_by = referred_by_profile
            user_profile.save()
            referred_by_profile.referrals_made += 1
            referred_by_profile.rewards_earned += Decimal('10.00')
            referred_by_profile.save()
            
            return JsonResponse({'success': True, 'message': 'Referral code submitted successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, "Login successful! Welcome back!")
            return redirect('index')  
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

def about(request):
    return render(request,'about.html')

def contact(request):
    return render(request,'contact.html')

def reference(request):
    return render(request,'reference.html')

def index(request):
    return render(request, 'index.html')

def welcome_page(request):
    return render(request, 'welcome.html')
 
def terms(request):
    return render(request,'terms.html')

@login_required
def profile_view(request):
    # Fetch user profile data
    profile = request.user.profile
    return render(request, 'profile.html', {'profile': request.user.profile})

def logout_view(request):
    logout(request)
    return redirect('login')

def services_view(request):
    services = Services.objects.all()
    return render(request, 'services.html', {'services': services})

@login_required
def payment_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.profile = request.user.profile
            payment.save()
            return redirect('payment_success')
    else:
        form = PaymentForm(user=request.user)
    return render(request, 'payment.html', {'form': form})

@login_required
def payment_success(request):
    return render(request, 'payment_success.html')

@login_required 
def product_scheme_manage(request):
    product_id = request.GET.get('id')  # Fetch `id` (service ID) from the request
    total = request.GET.get('total')  # Fetch `total` from the request

    # Fetch the product_id and total from the Services model
    if product_id:
        try:
            service = Services.objects.get(id=product_id)  # Fetch service based on ID
            product_id = service.product_id  # Extract product_id from the service
            total = service.total  # Extract total from the service
        except Services.DoesNotExist:
            product_id = None  # Reset to None if the service is not found
            total = None

    if request.method == 'POST':
        form = ProductSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)

            # Set the profile to the currently logged-in user's profile
            profile = Profile.objects.get(user=request.user)
            scheme.profile = profile  # Automatically set the profile field

            # Explicitly set product_id and total to ensure they are saved
            scheme.product_id = product_id
            scheme.total = total
            scheme.start_date = datetime.now()  # Set start date to current date

            # The end_date will be automatically calculated in the model during save
            scheme.save()  # Save the scheme, which will also calculate the end_date

            return redirect('payment_view')  # Redirect to the payment page
    else:
        # Pass initial values for product_id and total to the form
        form = ProductSchemeForm(initial={
            'product_id': product_id,
            'total': total,
        })

    # Render the template with the form and context
    return render(request, 'product_scheme_manage.html', {
        'form': form,
        'product_id': product_id,
        'total': total,
    })

def privacy_view(request):
   return render(request, 'privacy.html')

@login_required
def plans_view(request):
    profile = request.user.profile
    product_schemes = ProductScheme.objects.filter(profile=profile)

    plans = []
    for scheme in product_schemes:
        try:
            service = Services.objects.get(product_id=scheme.product_id)

            # Fetch all approved payments for this scheme
            approved_payments = Payment.objects.filter(product_scheme=scheme, payment_status='approved')
            approved_days = approved_payments.count()  # Count the number of approved payments

            # Calculate remaining days based on approved payments
            total_duration = (scheme.end_date - scheme.start_date).days
            remaining_days = max(0, total_duration - approved_days)

            latest_payment = Payment.objects.filter(product_scheme=scheme).order_by('-created_at').first()
            
            needs_payment = False
            
            total_paid = approved_payments.count() * scheme.investment  # Payment count × investment per period
            balance = max(0, scheme.total - total_paid)  # Ensure balance doesn't go negative

            if latest_payment:
                last_payment_date = latest_payment.created_at.date()
                today = date.today()

                if latest_payment.payment_status == 'approved':
                    # "Pay Now" should appear only after 12 AM (next day)
                    if last_payment_date < today:
                        needs_payment = True  

                elif latest_payment.payment_status == 'rejected':
                    needs_payment = True  # Rejected payments require reattempt

            plans.append({
                'img': service.img.url if service.img else None,
                'product_id': scheme.product_id,
                'title': service.title,
                'investment': scheme.investment,
                'balance': balance,  # Corrected balance calculation
                'remaining_days': remaining_days,  # Decreases based on payments
                'payment_status': latest_payment.payment_status if latest_payment else 'pending',
                'needs_payment': needs_payment,
            })
        except Services.DoesNotExist:
            continue

    context = {'plans': plans}
    return render(request, 'plans.html', context)

@login_required
def payment_history(request):
    profile = request.user.profile  # Get logged-in user's profile

    # Fetch all approved payments for the user
    payments = Payment.objects.filter(profile=profile, payment_status='approved').select_related('product_scheme')

    history = []
    for payment in payments:
        scheme = payment.product_scheme
        if scheme:
            try:
                service = Services.objects.get(product_id=scheme.product_id)  # Fetch service details
                history.append({
                    'product_id': service.product_id,
                    'title': service.title,
                    'investment': scheme.investment,
                    'balance': max(0, scheme.total - (scheme.investment * Payment.objects.filter(product_scheme=scheme, payment_status='approved').count())),
                    'transaction_id': payment.transaction_id,
                    'payment_paid_date': payment.created_at,
                })
            except Services.DoesNotExist:
                continue

    return render(request, "payment_history.html", {"history": history})
