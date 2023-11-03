from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

from .models import Tournament, Bracket
from .utils import inline_serializer, get_object
from .serializer import TournamentSerializer, BracketSerializer, AllBracketSerealizer
from .selectors import tournaments_list, get_brackets_for_tournamnet
from .services import create_tournament, create_bracket, update_bracket, update_tournament
from .permissions import IsTournamenOwnerOrReadOnly, IsBracketOwnerOrReadOnly, AuthMixin
from .pagination import get_paginated_response, LimitOffsetPagination

from rest_framework import parsers
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser



# class LargeResultsSetPagination(PageNumberPagination):
#     page_size = 9
#     page_size_query_param = 'page_size'
#     max_page_size = 1000


# class TournamentsAPIList(generics.ListCreateAPIView):
#     queryset = Tournament.objects.all().order_by('id')
#     serializer_class = TournamentSerializer
#     pagination_class = LargeResultsSetPagination

class TournamentsAPIList(APIView):
    class Pagination(LimitOffsetPagination):
        default_limit = 12
        
    class FilterSerializer(serializers.Serializer):
        id = serializers.CharField(required=False)
        title = serializers.CharField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Tournament
            fields = "__all__"
    
    def get(self, request):
        # Make sure the filters are valid, if passed
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        tournaments = tournaments_list(filters=filters_serializer.validated_data)

        # tournaments = Tournament.objects.all().order_by('id')

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=tournaments,
            request=request,
            view=self
        )

# class TournamentAPIView(generics.RetrieveAPIView): 
#     class OutputSerializer(serializers.ModelSerializer):
#         start_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M')
#         class Meta:
#             model = Tournament
#             fields = "__all__" 
#     queryset = Tournament.objects.all()
#     serializer_class = OutputSerializer
#     lookup_field = 'slug'

class TournamentAPIView(APIView): 
    
    class OutputSerializer(serializers.ModelSerializer):
        owner = serializers.StringRelatedField(required=False)
        start_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M')
        class Meta:
            model = Tournament
            fields = "__all__"  
        
    def get(self, request, slug):
        tournament = get_object(Tournament, slug=slug)
        serializer = self.OutputSerializer(tournament, context={'request': request})
        return Response(serializer.data)

# class TournamentCreateView(generics.CreateAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = (IsAuthenticated, )


class TournamentCreateView(APIView):
    permission_classes = (IsAuthenticated, )

    class InputSerializer(serializers.Serializer):

        title = serializers.CharField()
        content = serializers.CharField()
        participants = serializers.CharField()
        poster = serializers.ImageField(use_url=True, default=None)
        game = serializers.CharField()
        prize = serializers.FloatField()
        start_time = serializers.DateTimeField()
        creater_email = serializers.EmailField()

        type = serializers.ChoiceField(choices=['SE', 'DE', 'RR', 'SW'])
        secod_final = serializers.BooleanField(required=False)
        points_victory = serializers.IntegerField(required=False)
        points_loss = serializers.IntegerField(required=False)
        points_draw = serializers.IntegerField(required=False)

        time_managment = serializers.BooleanField()
        avg_game_time = serializers.IntegerField(required=False)
        max_games_number = serializers.IntegerField(required=False)
        break_between = serializers.IntegerField(required=False)
        mathes_same_time = serializers.IntegerField(required=False)

        tournament_type = serializers.BooleanField()
        group_type = serializers.ChoiceField(required=False, choices=['SE', 'DE', 'RR', 'SW'])
        compete_in_group = serializers.IntegerField(required=False)
        advance_from_group = serializers.IntegerField(required=False)
        groups_per_day = serializers.IntegerField(required=False)
        final_stage_time = serializers.BooleanField(required=False)

    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid()
        
        tournament = create_tournament(**serializer.validated_data)

        return Response(status=status.HTTP_201_CREATED)


# class TournamentDeleteAPIView(generics.DestroyAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'slug'

#     def delete(self, request, *args, **kwargs):
#         return self.destroy(request, *args, **kwargs)


class TournamentDeleteAPIView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)

    def delete(self, request, slug, *args, **kwargs):
        tournament = get_object(Tournament, slug=slug)
        self.check_object_permissions(request, tournament)
        tournament.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# class TournamentUpdateApiView(generics.UpdateAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'slug'


class TournamentUpdateApiView(APIView):
    permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)

    class InputSerializer(serializers.Serializer):
        title = serializers.CharField()
        content = serializers.CharField()
        poster = serializers.ImageField(use_url=True, default=None)
        game = serializers.CharField()
        prize = serializers.FloatField()
        start_time = serializers.DateTimeField()
        creater_email = serializers.EmailField()

    def patch(self, request, slug):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tournament = get_object(Tournament, slug=slug)
        self.check_object_permissions(request, tournament)
        tournament = update_tournament(tournament=tournament, data=serializer.validated_data)

        return Response(data={'slug': tournament.slug}, status=status.HTTP_200_OK)


# class BracketAPIView(generics.RetrieveAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer
#     lookup_field = 'id'

class BracketAPIView(APIView):
    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Bracket
            fields = "__all__"

    def get(self, request, id):
        bracket = get_object(Bracket, id=id)
        serializer = self.OutputSerializer(bracket)
        return Response(serializer.data)


# class BracketCreateView(generics.CreateAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer

class BracketCreateView(APIView):

    class InputSerializer(serializers.Serializer):
        type = serializers.ChoiceField(choices=['SE', 'DE', 'RR', 'SW'])
        participants = serializers.CharField()
        secod_final = serializers.BooleanField(required=False)
        points_victory = serializers.IntegerField(required=False)
        points_loss = serializers.IntegerField(required=False)
        points_draw = serializers.IntegerField(required=False)

    def post(self, request):
        input_serializer = self.InputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        bracket = create_bracket(**input_serializer.validated_data)

        return Response(data={'id': bracket.id}, status=status.HTTP_201_CREATED)


# class BracketUpdateAPIView(generics.UpdateAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer
#     permission_classes = ((IsBracketOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'id'


class BracketUpdateAPIView(APIView):
    permission_classes = ((IsBracketOwnerOrReadOnly|IsAdminUser),)

    class InputSerializer(serializers.Serializer):
        participants_from_group = serializers.IntegerField(required=False)
        final = serializers.BooleanField(required=False)

    def patch(self, request, id):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bracket = get_object(Bracket, id=id)
        self.check_object_permissions(request, bracket)
        bracket = update_bracket(bracket=bracket, match=request.data, data=serializer.validated_data)

        return Response(data={'bracket': bracket.bracket}, status=status.HTTP_200_OK)

# class AllBracketAPIView(generics.RetrieveAPIView): 
#     queryset = Tournament.objects.all()
#     serializer_class = AllBracketSerealizer
#     lookup_field = 'slug'


class AllBracketAPIView(APIView): 
    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = Bracket
            fields = "__all__"

    def get(self, request, slug):
        tournament = get_object(Tournament, slug=slug)
        brackets = get_brackets_for_tournamnet(tournament)
        serializer = self.OutputSerializer(brackets, many=True)

        return Response(serializer.data)