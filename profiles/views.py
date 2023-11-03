from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import UserModel
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.utils.translation import gettext_lazy as _
from .utils import send_email_for_reset
from .models import CustomUser, Profile
from rest_framework.response import Response
from .serializer import MyTokenObtainPairSerializer, RegisterSerializer, ProfileSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer, ImageChangeSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from .models import CustomUser
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import CustomUser
from rest_framework import status
from .permissions import IsProfileOwnerOrReadOnly


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserPasswordReset(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email = email)
        if user:
            send_email_for_reset(user.get())
        return Response({'status': 'OK'}, status=status.HTTP_200_OK)


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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        user = self.get_user(serializer.validated_data['uid'])

        if user is not None:
            if default_token_generator.check_token(user, token):
                password = serializer.validated_data['new_password']
                user.set_password(password)
                user.save()
                
        return Response({'status': 'OK'}, status=status.HTTP_200_OK)


class PasswordChangeAPIView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = (IsAuthenticated, )
    error_messages = {
        **SetPasswordForm.error_messages,
        "password_incorrect": _(
            "Your old password was entered incorrectly. Please enter it again."
        ),
    }
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        user = request.user
        if not user.check_password(old_password):
            raise ValidationError(
                self.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        else:
            password = serializer.validated_data['new_password']
            user.set_password(password)
            user.save()

        return Response({'status': 'OK'}, status=status.HTTP_200_OK)


class ImgChangeAPIView(generics.UpdateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ImageChangeSerializer
    permission_classes = (IsProfileOwnerOrReadOnly, )
    lookup_field = 'slug'


class RegisterAPIView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class ProfileAPIView(generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = 'slug'

class EmailVerify(View):

    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
        return redirect('http://localhost:3000/')
        

    @staticmethod
    def get_user(uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError,
                CustomUser.DoesNotExist, ValidationError):
            user = None
        return user

