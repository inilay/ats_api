from django.urls import path
from .views import TournamentUpdateApiView, TournamentsAPIList, TournamentAPIView, TournamentCreateView, BracketAPIView, BracketCreateView, AllBracketAPIView, TournamentDeleteAPIView, BracketUpdateAPIView


urlpatterns = [
    path('api/v1/tournament/<str:slug>/', TournamentAPIView.as_view()),
    path('api/v1/edit_tournament/<str:slug>/', TournamentUpdateApiView.as_view()),
    path('api/v1/delete_tournament/<str:slug>/', TournamentDeleteAPIView.as_view()),
    path('api/v1/tournaments/', TournamentsAPIList.as_view()),
    path('api/v1/create_tournament/', TournamentCreateView.as_view()),
    path('api/v1/bracket/<int:id>/', BracketAPIView.as_view()),
    path('api/v1/create_bracket/', BracketCreateView.as_view()),
    path('api/v1/tournament_brackets/<str:slug>/', AllBracketAPIView.as_view(), name='tournament_brackets'),
    path('api/v1/update_bracket/<int:id>/', BracketUpdateAPIView.as_view())
]