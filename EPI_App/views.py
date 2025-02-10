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
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
import razorpay
from .models import PaymentOrder
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import PaymentOrder, ProductScheme, Services, Payment
from datetime import date
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ProductScheme, Services, PaymentOrder

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
            profile_photo = request.FILES.get('profile_photo')
            
            profile = Profile.objects.create(
                user=user,
                referral_code=referral_code,
                referred_by=referred_by_profile,
                kyc_document=form.cleaned_data.get('kyc_document'),
                kyc_document_type=form.cleaned_data.get('kyc_document_type'),
                pan_card=form.cleaned_data.get('pan_card'),
                bank_passbook=form.cleaned_data.get('bank_passbook'),
                profile_photo=profile_photo,
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

def about1(request):
    return render(request,'about1.html')

def contact(request):
    return render(request,'contact.html')

def contact1(request):
    return render(request,'contact1.html')

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
    return redirect('welcome')

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

            return redirect('plans')  # Redirect to the payment page
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

# @login_required
# def plans_view(request):
#     profile = request.user.profile
#     product_schemes = ProductScheme.objects.filter(profile=profile)

#     plans = []
#     for scheme in product_schemes:
#         try:
#             service = Services.objects.get(product_id=scheme.product_id)
#             approved_payments = Payment.objects.filter(product_scheme=scheme, payment_status='approved')
            
#             # Calculate payment status and needs_payment
#             latest_payment = Payment.objects.filter(product_scheme=scheme).order_by('-created_at').first()
#             today = date.today()
            
#             # Default values
#             payment_status = 'pending'
#             needs_payment = False
#             total_paid = approved_payments.count() * scheme.investment
#             balance = max(0, scheme.total - total_paid)
            
#             if latest_payment:
#                 payment_status = latest_payment.payment_status
#                 last_payment_date = latest_payment.created_at.date()
                
#                 # Enable payment if:
#                 # 1. Payment was rejected
#                 # 2. Approved payment is older than today
#                 # 3. No approved payments yet
#                 if payment_status == 'rejected':
#                     needs_payment = True
#                 elif payment_status == 'approved' and last_payment_date < today:
#                     needs_payment = True
#             else:
#                 # No payments made yet
#                 payment_status = 'not_paid'
#                 needs_payment = True
            
#             # Calculate remaining days
#             total_duration = (scheme.end_date - scheme.start_date).days
#             remaining_days = max(0, total_duration - approved_payments.count())

#             plans.append({
#                 'id': scheme.id,  # Add scheme ID for payment URL
#                 'img': service.img.url if service.img else None,
#                 'product_id': scheme.product_id,
#                 'title': service.title,
#                 'investment': scheme.investment,
#                 'balance': balance,
#                 'remaining_days': remaining_days,
#                 'payment_status': payment_status,
#                 'needs_payment': needs_payment,
#             })
#         except Services.DoesNotExist:
#             continue

#     context = {'plans': plans}
#     return render(request, 'plans.html', context)

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
                
                # Fetch the count of approved payments up to the current payment date
                approved_payments_count = Payment.objects.filter(
                    product_scheme=scheme, 
                    payment_status='approved',
                    created_at__lte=payment.created_at  # Count payments made up to the current payment date
                ).count()

                # Calculate the balance considering only the payments made up to the current date
                total_paid = approved_payments_count * scheme.investment  # Approved payments till now
                balance = max(0, scheme.total - total_paid)  # Correct balance calculation
                
                history.append({
                    'product_id': service.product_id,
                    'title': service.title,
                    'investment': scheme.investment,
                    'balance': balance,
                    'transaction_id': payment.transaction_id,
                    'payment_paid_date': payment.created_at,
                })
            except Services.DoesNotExist:
                continue

    return render(request, "payment_history.html", {"history": history})

# @login_required
# def plans_view(request):
#     profile = request.user.profile
#     product_schemes = ProductScheme.objects.filter(profile=profile)

#     plans = []
#     for scheme in product_schemes:
#         try:
#             service = Services.objects.get(product_id=scheme.product_id)
#             approved_payments = PaymentOrder.objects.filter(product_id=scheme.product_id, payment_status='SUCCESSFUL')

#             # Fetch the latest payment
#             latest_payment = PaymentOrder.objects.filter(product_id=scheme.product_id).order_by('-created_at').first()
#             today = date.today()
            
#             # Default values
#             payment_status = 'PENDING'
#             needs_payment = False
#             total_paid = approved_payments.count() * scheme.investment
#             balance = max(0, scheme.total - total_paid)
#             last_payment_date = None 
            
#             if latest_payment:
#                 payment_status = latest_payment.payment_status
#                 last_payment_date = latest_payment.created_at.date()
                
#                 # Enable payment if:
#                 # 1. Payment was failed
#                 # 2. Last successful payment is older than today
#                 if payment_status == 'FAILED' or (payment_status == 'SUCCESSFUL' and last_payment_date < today):
#                     needs_payment = True
#             else:
#                 # No payments made yet
#                 payment_status = 'NOT_PAID'
#                 needs_payment = True
            
#             # Calculate remaining days
#             total_duration = (scheme.end_date - scheme.start_date).days
#             remaining_days = max(0, total_duration - approved_payments.count())

#             plans.append({
#                 'id': scheme.id,
#                 'img': service.img.url if service.img else None,
#                 'product_id': scheme.product_id,
#                 'title': service.title,
#                 'investment': scheme.investment,
#                 'balance': balance,
#                 'remaining_days': remaining_days,
#                 'payment_status': payment_status,
#                 'needs_payment': needs_payment,
#                 'last_payment_date': last_payment_date,
#             })
#         except Services.DoesNotExist:
#             continue

#     context = {'plans': plans}
#     return render(request, 'plans.html', context)

def paymentview(request, plan_id):
    if request.method == 'GET':
        try:
            # Get the plan and amount
            plan = ProductScheme.objects.get(id=plan_id)
            product_id = request.GET.get('product_id')
            profile = request.GET.get('profile')
            amount = int(plan.investment * 100)  # Convert to paise
            
            # Create Razorpay client and order
            client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
            order = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
            
            # Save order details in your database
            payment_order = PaymentOrder.objects.create(
                order_id=order['id'],
                amount=amount,
                currency='INR',
                payment_status='PENDING',
                product_id=product_id,
                profile=profile,
            )
            
            # Prepare data for the frontend
            payment_data = {
                'order_id': order['id'],
                'profile': profile,
                'amount': amount,
                'currency': 'INR',
                'key': settings.RAZOR_KEY_ID,
                'name': 'SAIORSE IT SOLUTIONS LLP',
                'description': 'Payment for Order',
                'callback_url': request.build_absolute_uri('/payment/callback/'),
            }
            
            return render(request, 'pay.html', {'payment_data': payment_data})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return HttpResponseBadRequest()

@login_required
def plans_view(request):
    profile = request.user.profile
    product_schemes = ProductScheme.objects.filter(profile=profile)

    plans = []
    today = date.today()

    for scheme in product_schemes:
        try:
            service = Services.objects.get(product_id=scheme.product_id)
            approved_payments = PaymentOrder.objects.filter(product_id=scheme.product_id, payment_status='SUCCESSFUL')

            # Fetch the latest payment
            latest_payment = PaymentOrder.objects.filter(product_id=scheme.product_id).order_by('-created_at').first()

            # Default values
            payment_status = 'NOT_PAID'
            needs_payment = True  # Assume payment is needed unless proven otherwise
            last_payment_date = None
            total_paid = approved_payments.count() * scheme.investment
            balance = max(0, scheme.total - total_paid)

            if latest_payment:
                payment_status = latest_payment.payment_status
                last_payment_date = latest_payment.created_at.date()

                # Enable payment if:
                # 1. Payment failed
                # 2. Last successful payment is older than today
                needs_payment = payment_status == 'FAILED' or (payment_status == 'SUCCESSFUL' and last_payment_date < today)
            else:
                # No payments made yet
                payment_status = 'NOT_PAID'
                needs_payment = True

            # Calculate remaining days
            total_duration = (scheme.end_date - scheme.start_date).days
            remaining_days = max(0, total_duration - approved_payments.count())

            plans.append({
                'id': scheme.id,
                'profile': profile,
                'img': service.img.url if service.img else None,
                'product_id': scheme.product_id,
                'title': service.title,
                'investment': scheme.investment,
                'balance': balance,
                'remaining_days': remaining_days,
                'payment_status': payment_status,
                'needs_payment': needs_payment,
                'last_payment_date': last_payment_date if last_payment_date else "No Payment Made",
            })
        
        except Services.DoesNotExist:
            continue

    return render(request, 'plans.html', {'plans': plans})

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        try:
            # Get payment data
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')
            
            # Verify payment signature
            client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
            payment_data = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            
            if client.utility.verify_payment_signature(payment_data):
                # Update payment status in database
                payment_order = PaymentOrder.objects.get(order_id=order_id)
                payment_order.payment_id = payment_id
                payment_order.payment_status = 'SUCCESSFUL'
                payment_order.save()
                
                return render(request, 'paymentsuccess.html')
            else:
                # Handle payment verification failure
                payment_order = PaymentOrder.objects.get(order_id=order_id)
                payment_order.payment_status = 'FAILED'
                payment_order.save()
                return render(request, 'paymentfailed.html')
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return HttpResponseBadRequest()