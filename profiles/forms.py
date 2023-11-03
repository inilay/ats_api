from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, UsernameField
from django.core.exceptions import ValidationError
from .utils import send_email_for_verify
from .models import CustomUser
from django import forms
from django.utils.translation import gettext_lazy as _


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    username = forms.CharField(label='User name')
    password1 = forms.CharField(label="Password")
    password2 = forms.CharField(label="Repeat password")

    widgets = {
        'email': forms.EmailInput(attrs={"class": "form-control"}),
        'username': forms.TextInput(attrs={"class": "form-control"}),
        'password1': forms.PasswordInput(attrs={"class": "form-control"}),
        'password2': forms.PasswordInput(attrs={"class": "form-control"})
    }

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

