from collections import defaultdict
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProfileUpdateForm, SignupForm, ProductSchemeForm, WithdrawalForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
import random
import string
from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Combo, Investment, Referral, Profile, ProductScheme, Services, Upto, Wishlist, WithdrawalRequest
from datetime import datetime, timedelta, date, timezone
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal
from django.db.models import Sum
from django.utils.timezone import now
from django.utils.timezone import get_current_timezone
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
import razorpay
from .models import PaymentOrder
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from .models import PaymentOrder, ProductScheme, Services
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ProductScheme, Services, PaymentOrder
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache, cache_control

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
        'total_rewards': profile.rewards_earned,
        'referred_investments': referred_data
    })

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

            # ✅ Check if the user already has a referrer
            if user_profile.referred_by:
                return JsonResponse({'success': False, 'message': 'You can only submit a referral code once.'})

            if user_profile == referred_by_profile:
                return JsonResponse({'success': False, 'message': 'You cannot refer yourself.'})

            # ✅ Set referred_by only once
            user_profile.referred_by = referred_by_profile
            user_profile.save()

            # ✅ Increase referral count and rewards
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

@login_required 
def product_scheme_manage(request):
    product_id = request.GET.get('id') # Fetch `id` (service ID) from the request
    total = request.GET.get('total') # Fetch `total` from the request

    # Fetch the product_id and total from the Services model
    if product_id:
        try:
            service = Services.objects.get(id=product_id) # Fetch service based on ID
            product_id = service.product_id # Extract product_id from the service
            total = service.total # Extract total from the service
        except Services.DoesNotExist:
            product_id = None # Reset to None if the service is not found
            total = None

    if request.method == 'POST':
        form = ProductSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)

            # Set the profile to the currently logged-in user's profile
            profile = Profile.objects.get(user=request.user)
            scheme.profile = profile # Automatically set the profile field

            # Explicitly set product_id and total to ensure they are saved
            scheme.product_id = product_id
            scheme.total = total
            scheme.start_date = datetime.now()  # Set start date to current date

            # The end_date will be automatically calculated in the model during save
            scheme.save() # Save the scheme, which will also calculate the end_date

            return redirect('plans') # Redirect to the payment page
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

def product_scheme_combo(request):
    product_id = request.GET.get('id') # Fetch id (service ID) from the request
    total = request.GET.get('total') # Fetch total from the request

    # Fetch the product_id and total from the Services model
    if product_id:
        try:
            combo = Combo.objects.get(id=product_id) # Fetch service based on ID
            product_id = combo.product_id # Extract product_id from the service
            total = combo.total # Extract total from the service
        except Combo.DoesNotExist:
            product_id = None # Reset to None if the service is not found
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
            scheme.start_date = datetime.now() # Set start date to current date

            # The end_date will be automatically calculated in the model during save
            scheme.save() # Save the scheme, which will also calculate the end_date

            return redirect('plans') # Redirect to the payment page
    else:
        # Pass initial values for product_id and total to the form
        form = ProductSchemeForm(initial={
            'product_id': product_id,
            'total': total,
        })

    # Render the template with the form and context
    return render(request, 'product_scheme_combo.html', {
        'form': form,
        'product_id': product_id,
        'total': total,
    })

@login_required
def product_scheme_upto(request):
    product_id = request.GET.get('id')  # Fetch id (service ID) from the request
    total = request.GET.get('total')  # Fetch total from the request

    # Fetch the product object and category
    upto22 = None
    category = None
    if product_id:
        try:
            upto22 = Upto.objects.get(id=product_id)  # Fetch product
            product_id = upto22.product_id  # Extract product_id
            total = upto22.total  # Extract total
            category = upto22.category  # Extract category
        except Upto.DoesNotExist:
            product_id = None
            total = None
            category = None

    if request.method == 'POST':
        form = ProductSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)
            profile = Profile.objects.get(user=request.user)
            scheme.profile = profile  # Assign user profile
            scheme.product_id = product_id
            scheme.total = total
            scheme.start_date = datetime.now()
            scheme.save()

            return redirect('plans')  # Redirect to plans page

    else:
        form = ProductSchemeForm(initial={
            'product_id': product_id,
            'total': total,
        })

    # Pass the category to the template
    return render(request, 'product_scheme_upto.html', {
        'form': form,
        'product_id': product_id,
        'total': total,
        'category': category,  # Now category is available in the template
    })

def privacy_view(request):
   return render(request, 'privacy.html')

def services_view(request):
    services = Services.objects.prefetch_related('images').all()
    user_favorites = []  

    if request.user.is_authenticated:
        user_favorites = Wishlist.objects.filter(user=request.user).values_list('service_id', flat=True)

    return render(request, 'services.html', {
        'services': services,
        'user_favorites': list(user_favorites),
    })

def combo_view(request):
    combo = Combo.objects.prefetch_related('images').all()
    user_favorites = []  

    if request.user.is_authenticated:
        user_favorites = Wishlist.objects.filter(user=request.user).values_list('combo_id', flat=True)

    return render(request, 'combo.html', {
        'combo': combo,
        'user_favorites': list(user_favorites),
    })

def upto_view(request):
    upto = Upto.objects.prefetch_related('images').all()
    user_favorites = []

    if request.user.is_authenticated:
        user_favorites = Wishlist.objects.filter(user=request.user).values_list('upto_id', flat=True)

    return render(request, 'upto.html', {
        'upto': upto,
        'user_favorites': list(user_favorites),
    })

@login_required
def comingsoon_view(request):
   return render(request, 'coming_soon.html')

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

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    if not request.user.is_authenticated:  # If user is not logged in, redirect to welcome page
        return redirect('welcome')
    return render(request, 'index.html')

def welcome_page(request):
    return render(request, 'welcome.html')
 
def terms(request):
    return render(request,'terms.html')

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def profile_view(request):
    if not request.user.is_authenticated:  # If user is not logged in, redirect them
        return redirect('welcome')  # Redirect to the welcome page instead of showing an error
    return render(request, 'profile.html', {'profile': request.user.profile})

def logout_view(request):
    logout(request)  # Logs out the user
    request.session.flush()  # Clears all session data
    response = redirect('welcome')  # Redirect to welcome page

    # Prevent browser from caching the page
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

@login_required
def payment_success(request):
    return render(request, 'payment_success.html')

@login_required
def payment_history(request):
    profile = request.user.profile  # Get the logged-in user's profile

    # Fetch all successful payments for the user in ascending order
    payments = PaymentOrder.objects.filter(profile=profile, payment_status='SUCCESSFUL').order_by('created_at')

    history = []
    scheme_balances = {}  # Store remaining balance per scheme
    scheme_remaining_days = {}  # Store remaining days per scheme

    for payment in payments:
        try:
            scheme = ProductScheme.objects.get(product_id=payment.product_id)

            # Identify scheme type
            try:
                service = Services.objects.get(product_id=payment.product_id)
                scheme_type = 'service'
            except Services.DoesNotExist:
                try:
                    service = Combo.objects.get(product_id=payment.product_id)
                    scheme_type = 'combo'
                except Combo.DoesNotExist:
                    try:
                        service = Upto.objects.get(product_id=payment.product_id)
                        scheme_type = 'upto'
                    except Upto.DoesNotExist:
                        continue

            payment_date = payment.created_at.astimezone(get_current_timezone()).date()
            product_id = scheme.product_id

            # Set initial balance and remaining days for the scheme if not already set
            if product_id not in scheme_balances:
                scheme_balances[product_id] = scheme.total  # Initial total balance
                scheme_remaining_days[product_id] = (scheme.end_date - scheme.start_date).days  # Total duration

            # Store previous balance & days for history tracking
            previous_balance = scheme_balances[product_id]
            previous_days = scheme_remaining_days[product_id]

            # Deduct investment amount per payment
            scheme_balances[product_id] -= scheme.investment  # Reduce by investment, not payment amount
            scheme_remaining_days[product_id] = max(0, scheme_remaining_days[product_id] - 1)  # Decrease remaining days

            history.append({
                'payment_date': payment_date,
                'plan': {
                    'title': service.title,
                    'investment': scheme.investment,
                    'balance': scheme_balances[product_id], # Store updated balance after deduction
                    'remaining_days': scheme_remaining_days[product_id], # Store updated remaining days
                    'last_payment_date': payment_date,
                },
                'service_total': scheme.total,
                'scheme_type': scheme_type,
            })

        except (ProductScheme.DoesNotExist, Services.DoesNotExist, Combo.DoesNotExist):
            continue
    
    return render(request, "payment_history.html", {"payment_history": history})

def paymentview(request, plan_id):
    if request.method == 'GET':
        try:
            # Get the plan and amount
            plan = ProductScheme.objects.get(id=plan_id)
            product_id = request.GET.get('product_id')
            
            # Get the profile of the logged-in user
            if request.user.is_authenticated:
                profile = get_object_or_404(Profile, user=request.user)  
            else:
                return JsonResponse({'error': 'User not authenticated'}, status=403)
            
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
            scheme_type = 'service'
        except Services.DoesNotExist:
            try:
                service = Combo.objects.get(product_id=scheme.product_id)
                scheme_type = 'combo'
            except Combo.DoesNotExist:
                try:
                    service = Upto.objects.get(product_id=scheme.product_id)
                    scheme_type = 'upto'
                except Upto.DoesNotExist:
                    continue

        approved_payments = PaymentOrder.objects.filter(product_id=scheme.product_id, payment_status='SUCCESSFUL')
        latest_payment = PaymentOrder.objects.filter(product_id=scheme.product_id).order_by('-created_at').first()

        payment_status = 'NOT_PAID'
        needs_payment = True
        last_payment_date = None
        total_paid = approved_payments.count() * scheme.investment
        balance = max(0, scheme.total - total_paid)

        if latest_payment:
            payment_status = latest_payment.payment_status
            last_payment_date = latest_payment.created_at.astimezone(tz=get_current_timezone()).date()
            needs_payment = payment_status == 'FAILED' or (payment_status == 'SUCCESSFUL' and last_payment_date < today)
        else:
            needs_payment = True

        total_duration = (scheme.end_date - scheme.start_date).days
        remaining_days = max(0, total_duration - approved_payments.count())

        plans.append({
            'id': scheme.id,
            'profile': profile,
            'img':service.images.first().image.url if service.images.exists() else None,  #
            'product_id': scheme.product_id,
            'title': service.title,
            'investment': scheme.investment,
            'balance': balance,
            'remaining_days': remaining_days,
            'payment_status': payment_status,
            'needs_payment': needs_payment,
            'last_payment_date': last_payment_date if last_payment_date else "No Payment Made",
            'scheme_type': scheme_type,
        })

    return render(request, 'plans.html', {'plans': plans})

@login_required
def edit_profile(request):
    profile = request.user.profile  # Get the logged-in user's profile

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, "edit_profile.html", {"form": form})

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

@login_required
def withdraw_request(request):
    user_profile = request.user.profile
    total_rewards = user_profile.rewards_earned  # Get user's total rewards

    if request.method == "POST":
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user

            if withdrawal.amount > total_rewards:
                form.add_error("amount", "You do not have enough rewards to withdraw this amount.")
            elif withdrawal.amount < Decimal('10.00'):
                form.add_error("amount", "Minimum withdrawal amount is ₹10.")
            else:
                # Calculate deductions
                withdrawal.tds_deduction = withdrawal.amount * Decimal('0.1')
                withdrawal.final_amount = withdrawal.amount - withdrawal.tds_deduction
                
                # Deduct the withdrawn amount from user's rewards
                user_profile.rewards_earned -= withdrawal.amount
                user_profile.save()  # Save updated rewards
                
                withdrawal.save()
                return redirect("withdrawal_history")
    else:
        form = WithdrawalForm()

    return render(request, "withdraw.html", {"form": form, "total_rewards": user_profile.rewards_earned})

@login_required
def withdrawal_history(request):
    withdrawals = WithdrawalRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "history.html", {"withdrawals": withdrawals})

@login_required
def add_to_wishlist(request, product_type, product_id):
    user = request.user
    wishlist_item = None
    created = False  # Track if a new item is added

    if product_type == 'service':
        product = get_object_or_404(Services, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, service=product)
    elif product_type == 'upto':
        product = get_object_or_404(Upto, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, upto=product)
    elif product_type == 'combo':
        product = get_object_or_404(Combo, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, combo=product)

    # If item exists and was NOT newly created, remove it (toggle behavior)
    if not created:
        wishlist_item.delete()
        return JsonResponse({"status": "removed", "product_id": product_id})

    return JsonResponse({"status": "added", "product_id": product_id})

@login_required
def remove_from_wishlist(request, wishlist_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_id, user=request.user)
    wishlist_item.delete()
    return redirect('wishlist')

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

# email sending for meassage for quirs 
@csrf_exempt
def send_email(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_email = data.get("email")  # User's email
            message = data.get("message")

            if not user_email or not message:
                return JsonResponse({"success": False, "error": "Email and message are required"}, status=400)

            email_subject = f"New Message from {user_email}"
            email_body = f"From: {user_email}\n\n{message}"

            recipient_list = ["epielio.com@gmail.com"]  # Epielio email

            # Send email to epielio.com (FROM user)
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=user_email,  # Sent from user to epielio
                recipient_list=recipient_list,
                fail_silently=False,
                html_message=None,
            )

            # Email body for user (copy, but "From: epielio.com")
            user_copy_body = f"From: epielio.com\n\n{message}"

            # Send a copy to the user (FROM epielio.com)
            send_mail(
                subject="Thank You for Messaging",
                message=f"Thank you for reaching out!\n\n{'we got a message in your mail we will contact you soon '}",
                from_email="no-reply@epielio.com",  # Now sending from epielio.com
                recipient_list=[user_email],  # Send to user
                fail_silently=False,
                html_message=None,
            )

            return JsonResponse({"success": True, "message": "Message sent successfully. A copy has been sent to your email."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

def chatbox(request):
    return render(request, 'chatbox.html')  # Ensure this file is inside your templates folder


def product_detail(request, product_type, product_id):
    if product_type == "service":
        product = get_object_or_404(Services, id=product_id)
    elif product_type == "combo":
        product = get_object_or_404(Combo, id=product_id)
    elif product_type == "upto":
        product = get_object_or_404(Upto, id=product_id)
    else:
        return render(request, '404.html')  # Handle invalid product type

    # Fetch related products based on category
    related_services = Services.objects.filter(category=product.category).exclude(id=product.id)[:4]
    combo_products = Combo.objects.filter(category=product.category).exclude(id=product.id)[:4]
    upto_products = Upto.objects.filter(category=product.category).exclude(id=product.id)[:4]

    return render(request, 'product_detail.html', {
        'product': product,
        'related_services': related_services,
        'combo_products': combo_products,
        'upto_products': upto_products
    })