from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Bracket, Round
from ..permissions import (
    IsAnonymousBracket,
)
from ..serializer import GetAllBracketsSerializer
from ..services.generation_services import create_bracket
from ..services.update_services import update_bracket
from ..utils import inline_serializer


class AnonymousBracketCreateView(APIView):
    class InputSerializer(serializers.Serializer):
        participants = serializers.CharField()
        advances_to_next = serializers.IntegerField()
        participant_in_match = serializers.IntegerField()
        bracket_type = serializers.IntegerField()
        points_victory = serializers.IntegerField(required=False)
        points_loss = serializers.IntegerField(required=False)
        points_draw = serializers.IntegerField(required=False)
        number_of_rounds = serializers.IntegerField(default=None)

    @transaction.atomic
    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        bracket = create_bracket(**input_serializer.validated_data, tournament=None, anonymous=True)

        return Response(data={"link": bracket.anonymous_bracket.link}, status=status.HTTP_201_CREATED)


class AnonymousBracketGetView(APIView):
    @transaction.atomic
    def get(self, request, link):
        bracket = get_object_or_404(
            Bracket.objects.select_related("anonymous_bracket").prefetch_related(
                Prefetch(
                    "rounds",
                    queryset=Round.objects.all().order_by("serial_number"),
                )
            ),
            anonymous_bracket__link=link,
        )
        output_serializer = GetAllBracketsSerializer(bracket)
        return Response(data=output_serializer.data, status=status.HTTP_200_OK)


class AnonymousBracketUpdateView(APIView):
    permission_classes = (IsAnonymousBracket,)

    class InputSerializer(serializers.Serializer):
        bracket_id = serializers.IntegerField()
        match_id = serializers.IntegerField()
        start_time = serializers.DateTimeField(required=False)
        state = serializers.CharField(required=False)

        match_results = serializers.DictField(
            child=inline_serializer(
                fields={
                    "participant": serializers.CharField(),
                    "score": serializers.IntegerField(),
                }
            )
        )

    @transaction.atomic
    def put(self, request):
        serializer = self.InputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bracket = get_object_or_404(
            Bracket.objects.prefetch_related(
                Prefetch(
                    "rounds",
                    queryset=Round.objects.all().order_by("serial_number"),
                )
            ).select_related("tournament", "anonymous_bracket"),
            id=serializer.validated_data.get("bracket_id"),
        )

        self.check_object_permissions(request, bracket)

        bracket = update_bracket(data=serializer.validated_data, bracket=bracket)
        serializer = GetAllBracketsSerializer(bracket)

        return Response(status=status.HTTP_200_OK, data=serializer.data)
