from django.db.models import Prefetch
from django.db.models.query import QuerySet

from .filters import TournamentFilter
from .models import Bracket, Match, MatchParticipantInfo, Round, Tournament


def get_brackets_for_tournamnet(tournament_id: int, **kwargs) -> QuerySet[Bracket]:
    brackets = Bracket.objects.prefetch_related(
        Prefetch(
            "rounds",
            queryset=Round.objects.prefetch_related(
                Prefetch(
                    "matches",
                    queryset=Match.objects.prefetch_related(
                        Prefetch(
                            "info",
                            queryset=MatchParticipantInfo.objects.only("participant_score", "participant"),
                        )
                    ).all(),
                )
            )
            .all()
            .order_by("serial_number"),
        )
    ).filter(tournament_id=tournament_id)

    return brackets


def tournaments_list(*, filters=None) -> QuerySet[Tournament]:
    filter = filters or {}
    query_set = Tournament.objects.select_related("owner").filter(type_id=1).order_by("-id")
    return TournamentFilter(filter, query_set).qs


def game_list(*, filters=None) -> list:
    game_list = Tournament.objects.distinct().values_list("game", flat=True)
    print(game_list)
    return game_list
