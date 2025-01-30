from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('about/', views.about,name='about'),
    path('profile/', views.profile_view, name='profile'),
    path('contact/', views.contact,name='contact'),
    path('services/', views.services_view, name='services'),
    path('reference/', views.reference,name='reference'),
    path('terms/', views.terms,name='terms'),
    path('logout/', views.logout_view, name='logout'),
    path('reference/', views.referral_view, name='reference'),
    path('payment/', views.payment_view,name='payment_view'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('product-scheme-manage/', views.product_scheme_manage, name='product_scheme_manage'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('plans/', views.plans_view, name='plans'),
    path('welcome/', views.welcome_page, name='welcome'),
]
