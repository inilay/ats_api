from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import UserModel
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from profiles.services import (
    create_push_token,
    create_subscription,
    create_user,
    delete_subscription,
)
from tournaments.models import Tournament

from .models import CustomUser, Profile
from .permissions import IsProfileOwnerOrReadOnly
from .serializer import (
    CreatePushTokenSerializer,
    CreateSubscriptionSerializer,
    DeleteSubscriptionSerializer,
    GetSubscriptionsSerializer,
    ImageChangeSerializer,
    MyTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ProfileSerializer,
    RegisterSerializer,
)
from .utils import send_email_for_reset


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserPasswordReset(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = CustomUser.objects.filter(email=email)
        if user:
            send_email_for_reset(user.get())
        return Response({"status": "OK"}, status=status.HTTP_200_OK)


class PasswordResetConfirmAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UserModel.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        user = self.get_user(serializer.validated_data["uid"])

        if user is not None:
            if default_token_generator.check_token(user, token):
                password = serializer.validated_data["new_password"]
                user.set_password(password)
                user.save()

        return Response({"status": "OK"}, status=status.HTTP_200_OK)


class PasswordChangeAPIView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = (IsAuthenticated,)
    error_messages = {
        **SetPasswordForm.error_messages,
        "password_incorrect": _("Your old password was entered incorrectly. Please enter it again."),
    }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data["old_password"]
        user = request.user
        if not user.check_password(old_password):
            raise ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        else:
            password = serializer.validated_data["new_password"]
            user.set_password(password)
            user.save()

        return Response({"status": "OK"}, status=status.HTTP_200_OK)


class ImgChangeAPIView(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ImageChangeSerializer
    permission_classes = (IsProfileOwnerOrReadOnly,)
    lookup_field = "slug"


class RegisterAPIView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    @transaction.atomic
    def post(self, request):
        input_serializer = self.serializer_class(data=request.data)
        if not input_serializer.is_valid():
            return Response(data=input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        print("call create")
        user = create_user(input_serializer.validated_data)
        output_serializer = self.serializer_class(user)
        return Response(data=output_serializer.data, status=status.HTTP_201_CREATED)


class ProfileAPIView(generics.RetrieveAPIView):
    queryset = Profile.objects.prefetch_related(
        Prefetch("tournaments", queryset=Tournament.objects.order_by("-id")),
        Prefetch("subscriptions", queryset=Tournament.objects.order_by("-id")),
    ).all()
    serializer_class = ProfileSerializer
    lookup_field = "slug"


class EmailVerify(APIView):
    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
        return redirect("http://localhost:3000/")

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist, ValidationError):
            user = None
        return user


class ReportAPIView(APIView):
    permission_classes = (AllowAny,)

    @transaction.atomic
    def post(self, request):
        return Response(status=status.HTTP_201_CREATED)


class GetSubscriptionsAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        profile = request.user.profile
        serializer = GetSubscriptionsSerializer(profile)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class CreateSubscriptionAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request):
        input_serializer = CreateSubscriptionSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        create_subscription(input_serializer.validated_data, request.user)
        return Response(status=status.HTTP_201_CREATED)


class DeleteSubscriptionAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def delete(self, request):
        input_serializer = DeleteSubscriptionSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        delete_subscription(input_serializer.validated_data, request.user)

        return Response(status=status.HTTP_200_OK)


class CreatePushTokenAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request):
        input_serializer = CreatePushTokenSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        create_push_token(input_serializer.validated_data, request.user)

        return Response(status=status.HTTP_201_CREATED)
