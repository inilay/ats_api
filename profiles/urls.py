from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import (
    CreatePushTokenAPIView,
    CreateSubscriptionAPIView,
    DeleteSubscriptionAPIView,
    EmailVerify,
    GetSubscriptionsAPIView,
    ImgChangeAPIView,
    MyTokenObtainPairView,
    PasswordChangeAPIView,
    PasswordResetConfirmAPIView,
    ProfileAPIView,
    RegisterAPIView,
    ReportAPIView,
    UserPasswordReset,
)

urlpatterns = [
    path("api/v1/token/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/register/", RegisterAPIView.as_view(), name="auth_register"),
    path("api/v1/profile/<str:slug>/", ProfileAPIView.as_view(), name="profile"),
    path("api/v1/password_reset/", UserPasswordReset.as_view(), name="password_reset"),
    path("api/v1/password_reset_confirm/", PasswordResetConfirmAPIView.as_view(), name="password_reset_confirm"),
    path("api/v1/img_change/<str:slug>/", ImgChangeAPIView.as_view(), name="password_change"),
    path("api/v1/password_change/", PasswordChangeAPIView.as_view(), name="password_change"),
    path("api/v1/create_report/", ReportAPIView.as_view(), name="create_report"),
    path("api/v1/get_subscriptions/", GetSubscriptionsAPIView.as_view(), name="subscriptions"),
    path("api/v1/create_subscription/", CreateSubscriptionAPIView.as_view(), name="create_subscription"),
    path("api/v1/delete_subscription/", DeleteSubscriptionAPIView.as_view(), name="delete_subscription"),
    path("api/v1/create_push_token/", CreatePushTokenAPIView.as_view(), name="create_push_token"),
    path("confirm_email/<uidb64>/<token>/", EmailVerify.as_view(), name="verify_email"),
]
