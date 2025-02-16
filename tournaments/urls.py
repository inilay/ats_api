from django.urls import path

from .views import (
    AllBracketAPIView,
    AnonymousBracketCreateView,
    AnonymousBracketGetView,
    AnonymousBracketUpdateView,
    BracketAPIView,
    BracketUpdateAPIView,
    CreateModeratorAPIView,
    DeleteModeratorAPIView,
    GamesApiView,
    TournamentAPIView,
    TournamentCreateView,
    TournamentDeleteAPIView,
    TournamentsAPIList,
    TournamentUpdateApiView,
)

urlpatterns = [
    path("api/v1/tournament/<str:link>/", TournamentAPIView.as_view()),
    path("api/v1/create_tournament/", TournamentCreateView.as_view()),
    path("api/v1/edit_tournament/<str:link>/", TournamentUpdateApiView.as_view()),
    path("api/v1/delete_tournament/<str:link>/", TournamentDeleteAPIView.as_view()),
    path("api/v1/tournaments/", TournamentsAPIList.as_view()),
    path("api/v1/games/", GamesApiView.as_view()),
    path("api/v1/create_moderator/", CreateModeratorAPIView.as_view(), name="create_moderator"),
    path("api/v1/delete_moderator/", DeleteModeratorAPIView.as_view(), name="delete_moderator"),
    path("api/v1/bracket/<int:id>/", BracketAPIView.as_view()),
    path("api/v1/tournament_brackets/<int:tournament_id>/", AllBracketAPIView.as_view(), name="tournament_brackets"),
    path("api/v1/update_bracket/", BracketUpdateAPIView.as_view()),
    path("api/v1/create_anonymous_bracket/", AnonymousBracketCreateView.as_view()),
    path("api/v1/anonymous_bracket/<str:link>/", AnonymousBracketGetView.as_view()),
    path("api/v1/update_anonymous_bracket/", AnonymousBracketUpdateView.as_view()),
]
