from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('',views.index,name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('about/', views.about,name='about'),
    path('about1/', views.about1,name='about1'),
    path('profile/', views.profile_view, name='profile'),
    path('submit-referral/', views.submit_referral, name='submit_referral'), 
    path('reference/', views.referral_view, name='reference'),
    path('contact/', views.contact,name='contact'),
    path('contact1/', views.contact1,name='contact1'),
    path('services/', views.services_view, name='services'),
    path('terms/', views.terms,name='terms'),
    path('logout/', views.logout_view, name='logout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('product-scheme-manage/', views.product_scheme_manage, name='product_scheme_manage'),
    path('product-scheme-combo/', views.product_scheme_combo, name='product_scheme_combo'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('plans/', views.plans_view, name='plans'),
    path('welcome/', views.welcome_page, name='welcome'),
    path('upto/', views.upto_view, name='upto'),
    path('coming-soon/', views.comingsoon_view, name='coming_soon'),
    path('combo/', views.combo_view, name='combo'),
    path('payment-history/', views.payment_history, name="payment_history"),
    path('payment/<int:plan_id>/', views.paymentview, name='paymentview'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('product-scheme-upto/', views.product_scheme_upto, name='product_scheme_upto'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # withdraw urls 
    path('withdraw/', views.withdraw_request, name='withdraw'),
    path('history/', views.withdrawal_history, name='withdrawal_history'),

    # wishlist 
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<str:product_type>/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:wishlist_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]
