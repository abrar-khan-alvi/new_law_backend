from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    ResendVerificationView,
    UserListView,
    VerifyEmailView,
    VerifyOfficerView,
    AgencyCreateView,
)

urlpatterns = [
    # Agency configuration
    path('agencies/', AgencyCreateView.as_view()),
    # Registration & email verification
    path('register/', RegisterView.as_view()),
    path('verify-email/', VerifyEmailView.as_view()),
    path('resend-verification/', ResendVerificationView.as_view()),

    # Login / token lifecycle
    path('login/', LoginView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),

    # Profile & password
    path('profile/', ProfileView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('password-reset/', PasswordResetRequestView.as_view()),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view()),

    # Admin
    path('verify-officer/<int:pk>/', VerifyOfficerView.as_view()),
    path('users/', UserListView.as_view()),
]
