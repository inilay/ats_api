from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import UserPasswordReset, EmailVerify, \
    ProfileAPIView, PasswordResetConfirmAPIView, PasswordChangeAPIView, MyTokenObtainPairView, RegisterAPIView, ImgChangeAPIView



urlpatterns = [
    path('api/v1/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/register/', RegisterAPIView.as_view(), name='auth_register'),
    path('api/v1/profile/<str:slug>/', ProfileAPIView.as_view(), name='profile'),
    path('api/v1/password_reset/', UserPasswordReset.as_view(), name='password_reset'),
    path('api/v1/password_reset_confirm/', PasswordResetConfirmAPIView.as_view(), name="password_reset_confirm"),
    path('api/v1/img_change/<str:slug>/', ImgChangeAPIView.as_view(), name="password_change"),
    path("api/v1/password_change/", PasswordChangeAPIView.as_view(), name="password_change"),
    path('confirm_email/<uidb64>/<token>/', EmailVerify.as_view(), name="verify_email"),


]