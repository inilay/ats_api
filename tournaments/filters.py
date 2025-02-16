import django_filters

from .models import Tournament


class TournamentFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    game = django_filters.CharFilter(field_name="game", lookup_expr="icontains")

    class Meta:
        model = Tournament
        fields = ("title", "game")
