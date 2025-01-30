from django.shortcuts import render,redirect, get_object_or_404
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
from decimal import Decimal
from .models import Payment, Referral, Profile, ProductScheme, Services
from datetime import datetime, timedelta, date


# Create your views here.
def generate_referral_code():
    """Generate a unique 8-character referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirect authenticated users to home

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            #print("Form is valid")  # Debug message
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create profile with referral code and save KYC details
            referral_code = generate_referral_code()
            referred_by = request.POST.get('referred_by', None)

            referred_by_profile = None
            if referred_by:
                try:
                    referred_by_profile = Profile.objects.get(referral_code=referred_by)
                except Profile.DoesNotExist:
                    referred_by_profile = None

            #print(f"Generated referral code: {referral_code}")  # Debug message
            profile = Profile.objects.create(
                user=user,
                referral_code=referral_code,
                referred_by=request.POST.get('referred_by', None),
                kyc_document = form.cleaned_data.get('kyc_document'),
                kyc_document_type = form.cleaned_data.get('kyc_document_type'),
                pan_card=form.cleaned_data.get('pan_card'),
                bank_passbook=form.cleaned_data.get('bank_passbook'),
            )

            # Track referral and rewards
            if referred_by_profile:
                referred_by_profile.referrals_made += 1
                referred_by_profile.rewards_earned += 10.00  # Example reward
                referred_by_profile.save()
                Referral.objects.create(referred_by=referred_by_profile, referred_user=user)

            auth_login(request, user)
            messages.success(request, "Signup successful! Welcome aboard!")
            return JsonResponse({'success': True, 'referral_code': referral_code})
        
        else:
            # Process form errors and send them as JSON response
            errors = {
                field: [error['message'] for error in error_list] 
                for field, error_list in form.errors.get_json_data().items()
            }
            return JsonResponse({'success': True, 'referral_code': referral_code})

    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})


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
    return render(request, 'profile.html', {'profile': profile})

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
def referral_view(request):
    user_profile = Profile.objects.get(user=request.user)

    if not user_profile.referral_code:
        user_profile.referral_code = generate_referral_code()

    referrals = Referral.objects.filter(referred_by=user_profile)
    referral_count = referrals.count()
    total_rewards = user_profile.rewards_earned

    referred_persons = [
        {
            'name': referral.referred_user.username,
            'timestamp': referral.timestamp,
        }
        for referral in referrals
    ]

    context = {
        'referral_code': user_profile.referral_code,
        'referral_count': referral_count,
        'total_rewards': total_rewards,
        'referred_persons': referred_persons,
    }
    return render(request, 'refar.html', context)

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
    profile = request.user.profile  # Get the user's profile
    product_schemes = ProductScheme.objects.filter(profile=profile)  # Get all product schemes

    plans = []
    for scheme in product_schemes:
        try:
            service = Services.objects.get(product_id=scheme.product_id)  # Get service details

            # Get the latest payment for this scheme
            latest_payment = Payment.objects.filter(product_scheme=scheme).order_by('-created_at').first()
            
            # Determine if the user needs to pay today
            needs_payment = False
            balance = scheme.total  # Default: show total amount unless payment is approved
            
            if latest_payment:
                if latest_payment.payment_status == 'approved':
                    balance = scheme.total - scheme.investment  # Update balance only if approved
                elif latest_payment.payment_status == 'rejected':
                    needs_payment = True  # User needs to pay again if rejected
                else:
                    last_payment_date = latest_payment.created_at.date()
                    today = date.today()
                    if last_payment_date < today:  # Daily investment check
                        needs_payment = True  # User needs to pay again today

            remaining_days = (scheme.end_date - date.today()).days  # Calculate remaining days

            plans.append({
                'img': service.img.url if service.img else None,  
                'product_id': scheme.product_id,
                'title': service.title,
                'investment': scheme.investment,
                'balance': balance,  # Balance updates only if payment is approved
                'remaining_days': max(0, remaining_days),
                'payment_status': latest_payment.payment_status if latest_payment else 'pending',
                'needs_payment': needs_payment,
            })
        except Services.DoesNotExist:
            continue

    context = {'plans': plans}
    return render(request, 'plans.html', context)
