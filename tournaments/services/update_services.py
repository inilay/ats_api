
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from profiles.models import Profile
from tournaments.services.de_services import update_de_bracket
from tournaments.services.rr_services import update_rr_bracket
from tournaments.services.se_services import update_se_bracket
from tournaments.services.sw_services import update_sw_bracket

from ..models import (
    Bracket,
    Tournament,
)
from ..utils import model_update


def create_moderator(validated_data: dict) -> Profile:
    username = validated_data.get("username")
    tournament_id = validated_data.get("tournament_id")

    profile = get_object_or_404(Profile.objects.select_related("user"), user__username=username)
    tournament = get_object_or_404(Tournament, id=tournament_id)
    tournament.moderators.add(profile)

    return profile


def delete_moderator(validated_data: dict) -> None:
    username = validated_data.get("username")
    tournament_id = validated_data.get("tournament_id")

    profile = get_object_or_404(Profile.objects.select_related("user"), user__username=username)
    tournament = get_object_or_404(Tournament, id=tournament_id)
    tournament.moderators.remove(profile)

    return None


def update_tournament(*, tournament: Tournament, data) -> Tournament:
    non_side_effect_fields = ["content", "poster", "game", "start_time"]
    tournament, has_update = model_update(instance=tournament, fields=non_side_effect_fields, data=data)

    if tournament.title != data["title"]:
        tournament.title = data["title"]
        tournament.link = slugify(data["title"])
        tournament.full_clean()
        tournament.save(update_fields=["title", "link"])

    return tournament


def update_bracket(*, data: dict, bracket: Bracket) -> Bracket:
    if bracket.bracket_type.name == "SE":
        update_se_bracket(data)
    elif bracket.bracket_type.name == "DE":
        update_de_bracket(data)
    elif bracket.bracket_type.name == "RR":
        update_rr_bracket(data)
    elif bracket.bracket_type.name == "SW":
        update_sw_bracket(data)

    return bracket
