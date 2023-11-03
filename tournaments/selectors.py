from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Tournament, Bracket
from .filters import TournamentFilter


def get_brackets_for_tournamnet(tournament:Tournament, **kwargs) -> QuerySet[Bracket]:
    return tournament.brackets.all()

def tournaments_list(*, filters=None) -> QuerySet[Tournament]:
    filter = filters or {}
    query_set = Tournament.objects.all()

    return TournamentFilter(filter, query_set).qs