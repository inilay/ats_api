from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Tournament
from ..pagination import LimitOffsetPagination, get_paginated_response
from ..permissions import IsTournamenOwnerOrReadOnly
from ..selectors import game_list, tournaments_list
from ..services.generation_services import create_tournament
from ..services.update_services import create_moderator, delete_moderator, update_tournament
from ..utils import get_object


class TournamentsAPIList(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        default_offset = 0

    class FilterSerializer(serializers.Serializer):
        title = serializers.CharField(required=False)
        game = serializers.CharField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Tournament
            fields = "__all__"

    def get(self, request):
        # Make sure the filters are valid, if passed
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        tournaments = tournaments_list(filters=filters_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=tournaments,
            request=request,
            view=self,
        )


class TournamentAPIView(APIView):
    class OutputSerializer(serializers.ModelSerializer):
        owner = serializers.StringRelatedField(required=False)
        start_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")
        moderators = serializers.StringRelatedField(many=True)

        class Meta:
            model = Tournament
            fields = "__all__"

    def get(self, request, link):
        tournament = get_object(Tournament, link=link)
        serializer = self.OutputSerializer(tournament, context={"request": request})
        return Response(serializer.data)


class TournamentCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    class InputSerializer(serializers.Serializer):
        # tournament
        title = serializers.CharField()
        content = serializers.CharField(default=None)
        participants = serializers.CharField()
        poster = serializers.ImageField(use_url=True, default=None)
        game = serializers.CharField()
        start_time = serializers.DateTimeField()
        private = serializers.BooleanField()
        # bracket
        advances_to_next = serializers.IntegerField()
        participant_in_match = serializers.IntegerField()
        bracket_type = serializers.IntegerField()
        points_victory = serializers.IntegerField(required=False)
        points_loss = serializers.IntegerField(required=False)
        points_draw = serializers.IntegerField(required=False)
        number_of_rounds = serializers.IntegerField(default=None)
        # group bracket
        tournament_type = serializers.IntegerField(required=False)
        group_type = serializers.IntegerField(required=False)
        participant_in_group = serializers.IntegerField(required=False)
        advance_from_group = serializers.IntegerField(required=False)

    @transaction.atomic
    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        create_tournament(
            **serializer.validated_data,
            user=request.user,
        )
        return Response(status=status.HTTP_201_CREATED)


class TournamentDeleteAPIView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly | IsAdminUser),)

    @transaction.atomic
    def delete(self, request, link, *args, **kwargs):
        tournament = get_object(Tournament, link=link)
        self.check_object_permissions(request, tournament)
        tournament.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TournamentUpdateApiView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly | IsAdminUser),)

    class InputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        poster = serializers.ImageField(use_url=True, default=None)
        game = serializers.CharField()
        start_time = serializers.DateTimeField()
        creater_email = serializers.EmailField()

    @transaction.atomic
    def patch(self, request, link):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tournament = get_object(Tournament, link=link)
        self.check_object_permissions(request, tournament)
        tournament = update_tournament(tournament=tournament, data=serializer.validated_data)

        return Response(data={"link": tournament.link}, status=status.HTTP_200_OK)


class CreateModeratorAPIView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly | IsAdminUser),)

    class InputSerializer(serializers.Serializer):
        tournament_id = serializers.IntegerField()
        username = serializers.CharField()

    @transaction.atomic
    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        create_moderator(serializer.validated_data)
        return Response(status=status.HTTP_201_CREATED)


class DeleteModeratorAPIView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly | IsAdminUser),)

    class InputSerializer(serializers.Serializer):
        tournament_id = serializers.IntegerField()
        username = serializers.CharField()

    @transaction.atomic
    def delete(self, request):
        serializer = self.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        delete_moderator(serializer.validated_data)
        return Response(status=status.HTTP_200_OK)


class GamesApiView(APIView):
    def get(self, requet):
        games = game_list()
        return Response(games)
