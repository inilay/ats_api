import math
import uuid
from functools import partial

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError as RestValidationError

from profiles.models import CustomUser
from tournaments.services.auxiliary_services import create_tournament_notification
from tournaments.services.de_services import create_de_bracket
from tournaments.services.rr_services import create_rr_bracket
from tournaments.services.se_services import create_se_bracket
from tournaments.services.sw_services import create_sw_bracket

from ..models import (
    AnonymousBracket,
    Bracket,
    GroupBracketSettings,
    RRBracketSettings,
    SEBracketSettings,
    SWBracketSettings,
    Tournament,
)
from ..utils import clear_participants


def create_bracket(
    bracket_type: int,
    tournament: Tournament,
    participant_in_match: int,
    participants: list,
    shuffle: bool,
    advances_to_next: int = 1,
    points_loss: int = 0,
    points_draw: int = 0,
    points_victory: int = 0,
    number_of_rounds: int = 0,
    anonymous: bool = False,
) -> Bracket:
    bracket = Bracket.objects.create(
        tournament=tournament,
        bracket_type_id=bracket_type,
        participant_in_match=participant_in_match,
    )

    if anonymous:
        participants = clear_participants(participants, shuffle)
        unique_id = uuid.uuid4()
        AnonymousBracket.objects.create(bracket=bracket, link=unique_id)

    if bracket_type in [1, 5, 9]:
        settings = SEBracketSettings.objects.create(bracket=bracket, advances_to_next=advances_to_next)
        create_se_bracket(bracket, participants, settings)
    elif bracket_type in [2, 6, 10]:
        create_de_bracket(bracket, participants)
    elif bracket_type in [3, 7, 11]:
        settings = RRBracketSettings.objects.create(
            bracket=bracket,
            points_per_loss=points_loss,
            points_per_draw=points_draw,
            points_per_victory=points_victory,
        )
        create_rr_bracket(bracket, participants)
    elif bracket_type in [4, 8, 12]:
        settings = SWBracketSettings.objects.create(
            bracket=bracket,
            points_per_loss=points_loss,
            points_per_draw=points_draw,
            points_per_victory=points_victory,
        )
        create_sw_bracket(bracket, participants, number_of_rounds)

    return bracket


def create_tournament(
    *,
    title: str,
    content: str,
    poster,
    game: str,
    start_time,
    bracket_type: int,
    user: CustomUser,
    participants: str,
    advances_to_next: int,
    participant_in_match,
    points_victory: int,
    points_loss: int,
    points_draw: int,
    number_of_rounds: int,
    tournament_type: int,
    participant_in_group: int,
    advance_from_group: int,
    group_type: int,
    private: bool,
    shuffle: bool,
) -> Tournament:
    if private:
        unique_id = uuid.uuid4()
        link = unique_id
    else:
        link = slugify(title)

    if Tournament.objects.filter(link=link).exists():
        raise RestValidationError(detail={"error": "Tournament with the same title already exists"})

    tournament = Tournament.objects.create(
        title=title,
        content=content,
        poster=poster,
        link=link,
        game=game,
        start_time=start_time,
        owner=user.profile,
        type_id=2 if private else 1,
    )

    participants = clear_participants(participants, shuffle)

    if tournament_type == 1:
        group_brackets = []
        start = 0
        end = participant_in_group

        number_of_group = math.ceil(len(participants) / participant_in_group)
        final_bracket = create_bracket(
            bracket_type,
            tournament,
            participant_in_match,
            ["---" for i in range(number_of_group * advance_from_group)],
            shuffle,
            advances_to_next,
            points_loss,
            points_draw,
            points_victory,
            number_of_rounds,
        )
        missing_participants = participant_in_group * number_of_group - len(participants)

        for _ in range(missing_participants):
            participants.append("---")

        for _ in range(number_of_group):
            bracket = create_bracket(
                group_type,
                tournament,
                participant_in_match,
                participants[start:end],
                shuffle,
                advances_to_next,
                points_loss,
                points_draw,
                points_victory,
                number_of_rounds,
            )
            group_brackets.append(bracket)
            start += participant_in_group
            end += participant_in_group

        group_settings = GroupBracketSettings.objects.create(
            final_bracket=final_bracket,
            participant_in_group=participant_in_group,
            advance_from_group=advance_from_group,
        )
        group_settings.group_brackets.set(group_brackets)

    else:
        create_bracket(
            bracket_type,
            tournament,
            participant_in_match,
            participants,
            shuffle,
            advances_to_next,
            points_loss,
            points_draw,
            points_victory,
            number_of_rounds,
        )

    now = timezone.now()
    minimum_start_time = now + timezone.timedelta(hours=24)

    if start_time < minimum_start_time and start_time > now:
        transaction.on_commit(partial(create_tournament_notification, tournament=tournament, start_time=start_time))

    return
