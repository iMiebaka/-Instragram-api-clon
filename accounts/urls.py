from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.authtoken import views as api_auth_views

app_name = 'accounts'
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login, name="login"),
    path("login-with-otp/", views.login_with_otp, name="login_with_otp"),
    path("api_token_auth/", api_auth_views.obtain_auth_token, name="obtain_token"),
    path("logout/", views.logout_view, name="logout_view"),    
    path("change-password/", views.change_password, name="change_password"),    
    path("activate/request-otp/", views.getopt, name="OTP_GEN"),
    path("activate/verify-otp/", views.verifyopt, name="OTP_CHECK"),
    path("activate/verify-account-sms/", views.verify_account_sms, name="verify_account_sms"),
    path("activate/verify-account-email/", views.verify_account_email, name="verify_account_email"),
    path('modify-account/', views.modify_account, name='modify_account'),
]