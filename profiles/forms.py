from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    username = forms.CharField(label="User name")
    password1 = forms.CharField(label="Password")
    password2 = forms.CharField(label="Repeat password")

    widgets = {
        "email": forms.EmailInput(attrs={"class": "form-control"}),
        "username": forms.TextInput(attrs={"class": "form-control"}),
        "password1": forms.PasswordInput(attrs={"class": "form-control"}),
        "password2": forms.PasswordInput(attrs={"class": "form-control"}),
    }

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "email", "password1", "password2")
