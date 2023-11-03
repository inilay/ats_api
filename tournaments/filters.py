import django_filters

from .models import Tournament


class TournamentFilter(django_filters.FilterSet):
    class Meta:
        model = Tournament
        fields = ("id", "title")