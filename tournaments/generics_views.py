

# class LargeResultsSetPagination(PageNumberPagination):
#     page_size = 9
#     page_size_query_param = 'page_size'
#     max_page_size = 1000


# class TournamentsAPIList(generics.ListCreateAPIView):
#     queryset = Tournament.objects.all().order_by('id')
#     serializer_class = TournamentSerializer
#     pagination_class = LargeResultsSetPagination

# class TournamentAPIView(generics.RetrieveAPIView):
#     class OutputSerializer(serializers.ModelSerializer):
#         start_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M')
#         class Meta:
#             model = Tournament
#             fields = "__all__"
#     queryset = Tournament.objects.all()
#     serializer_class = OutputSerializer
#     lookup_field = 'slug'

# class TournamentCreateView(generics.CreateAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = (IsAuthenticated, )

# class TournamentDeleteAPIView(generics.DestroyAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'slug'

#     def delete(self, request, *args, **kwargs):
#         return self.destroy(request, *args, **kwargs)

# class TournamentUpdateApiView(generics.UpdateAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = TournamentSerializer
#     permission_classes = ((IsTournamenOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'slug'

# class BracketAPIView(generics.RetrieveAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer
#     lookup_field = 'id'

# class BracketCreateView(generics.CreateAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer

# class BracketUpdateAPIView(generics.UpdateAPIView):
#     queryset = Bracket.objects.all()
#     serializer_class = BracketSerializer
#     permission_classes = ((IsBracketOwnerOrReadOnly|IsAdminUser),)
#     lookup_field = 'id'

# class AllBracketAPIView(generics.RetrieveAPIView):
#     queryset = Tournament.objects.all()
#     serializer_class = AllBracketSerealizer
#     lookup_field = 'slug'
