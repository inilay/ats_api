from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError as RestValidationError

from profiles.models import CustomUser, PushToken
from tournaments.models import Tournament


def create_subscription(validated_data: dict, user: CustomUser) -> None:
    tournament = get_object_or_404(Tournament, id=validated_data.get("tournament_id"))
    user.profile.subscriptions.add(tournament)
    # celery_send_tournament_notificataion.delay_on_commit(280)
    # print('pull task')
    return None


def create_push_token(validated_data: dict, user: CustomUser) -> PushToken:
    push_token = PushToken.objects.create(token=validated_data.get("token"), profile=user.profile)

    return push_token


def delete_subscription(validated_data: dict, user: CustomUser) -> None:
    tournament = get_object_or_404(Tournament, id=validated_data.get("tournament_id"))
    user.profile.subscriptions.remove(tournament)

    return None


def create_user(validated_data: dict):
    if CustomUser.objects.filter(username=validated_data.get("username")).exists():
        raise RestValidationError(detail={"error": "User with the same name already exists"})
    elif CustomUser.objects.filter(email=validated_data.get("email")).exists():
        raise RestValidationError(detail={"error": "User with the same email already exists"})
    user = CustomUser.objects.create(username=validated_data["username"], email=validated_data["email"])

    user.set_password(validated_data["password"])
    user.save()
    # send_email_for_verify(user)

    return user
