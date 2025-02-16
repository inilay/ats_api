from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Bracket, Round
from ..permissions import IsTournamentModeratorOrOwner
from ..selectors import get_brackets_for_tournamnet
from ..serializer import GetAllBracketsSerializer
from ..services.update_services import update_bracket
from ..utils import get_object, inline_serializer


class BracketAPIView(APIView):
    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Bracket
            fields = "__all__"

    def get(self, request, id):
        bracket = get_object(Bracket, id=id)
        serializer = self.OutputSerializer(bracket)
        print("bracket")
        return Response(serializer.data)


class BracketUpdateAPIView(APIView):
    permission_classes = (IsTournamentModeratorOrOwner,)

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
            ).select_related("tournament"),
            id=serializer.validated_data.get("bracket_id"),
        )

        self.check_object_permissions(request, bracket)

        bracket = update_bracket(data=serializer.validated_data, bracket=bracket)
        serializer = GetAllBracketsSerializer(bracket)

        return Response(status=status.HTTP_200_OK, data=serializer.data)


class AllBracketAPIView(APIView):
    def get(self, request, tournament_id):
        brackets = get_brackets_for_tournamnet(tournament_id=tournament_id)
        serializer = GetAllBracketsSerializer(brackets, many=True)

        return Response(status=status.HTTP_200_OK, data=serializer.data)
