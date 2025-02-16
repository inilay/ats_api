from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as RestValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from tournaments.serializer import TournamentSerializer

from .models import CustomUser, Profile


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        # ...
        return token


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise RestValidationError(detail={"error": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(username=validated_data["username"], email=validated_data["email"])

        user.set_password(validated_data["password"])
        user.save()
        # send_email_for_verify(user)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username", "date_joined", "email"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    tournaments = TournamentSerializer(many=True)
    subscriptions = TournamentSerializer(many=True)

    class Meta:
        model = Profile
        fields = "__all__"


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    re_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    re_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["re_new_password"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs


class ImageChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("user_icon",)


class GetSubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("subscriptions",)


class CreateSubscriptionSerializer(serializers.Serializer):
    tournament_id = serializers.IntegerField()


class DeleteSubscriptionSerializer(serializers.Serializer):
    tournament_id = serializers.IntegerField()
