import json

from rest_framework import serializers

from profiles.models import Profile

from .brackets import DoubleEl, MultiStage, RoundRobin, SingleEl, Swiss
from .models import Bracket, Tournament
from .utils import clear_participants


class TournamentSerializer(serializers.ModelSerializer):
    link = serializers.CharField(required=False)
    owner = serializers.StringRelatedField(required=False)
    start_time = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")

    class Meta:
        model = Tournament
        fields = [
            "id",
            "link",
            "title",
            "content",
            "poster",
            "game",
            "created_at",
            "start_time",
            "owner",
        ]

    def create(self, validated_data):
        if self.initial_data.get("tournamentType") == "1":
            multi_stage = MultiStage(
                clear_participants(validated_data.get("participants")),
                {
                    "compete_in_group": int(self.initial_data.get("compete_in_group")),
                    "advance_from_group": int(self.initial_data.get("advance_from_group")),
                    "type": self.initial_data.get("type"),
                    "group_type": self.initial_data.get("group_type"),
                },
                {
                    "time_managment": json.loads(self.initial_data.get("time_managment")),
                    "start_time": validated_data.get("start_time"),
                    "avg_game_time": int(self.initial_data.get("avg_game_time")),
                    "max_games_number": int(self.initial_data.get("max_games_number")),
                    "break_between": int(self.initial_data.get("break_between")),
                    "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    "groups_per_day": int(self.initial_data.get("groups_per_day")),
                    "final_stage_time": json.loads(self.initial_data.get("final_stage_time")),
                },
                {
                    "win": int(self.initial_data.get("points_victory")),
                    "loss": int(self.initial_data.get("points_loss")),
                    "draw": int(self.initial_data.get("points_draw")),
                },
                json.loads(self.initial_data.get("secod_final")),
            )

            brackets = multi_stage.create_multi_stage_brackets()
            tournament = Tournament.objects.create(
                **validated_data,
                owner=Profile.objects.get(user__email=self.initial_data.get("creater_email")),
            )

            for i in brackets[0:-1]:
                Bracket.objects.create(
                    tournament=tournament,
                    bracket=i,
                    final=False,
                    type=self.initial_data.get("group_type"),
                )

            Bracket.objects.create(
                tournament=tournament,
                bracket=brackets[-1],
                participants_from_group=int(self.initial_data.get("advance_from_group")),
                type=self.initial_data.get("type"),
            )

        else:
            if self.initial_data.get("type") == "SE":
                single_el = SingleEl(
                    clear_participants(validated_data.get("participants")),
                    {
                        "time_managment": json.loads(self.initial_data.get("time_managment")),
                        "start_time": validated_data.get("start_time"),
                        "avg_game_time": int(self.initial_data.get("avg_game_time")),
                        "max_games_number": int(self.initial_data.get("max_games_number")),
                        "break_between": int(self.initial_data.get("break_between")),
                        "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    },
                    json.loads(self.initial_data.get("secod_final")),
                )
                print(
                    {
                        "time_managment": json.loads(self.initial_data.get("time_managment")),
                        "start_time": validated_data.get("start_time"),
                        "avg_game_time": int(self.initial_data.get("avg_game_time")),
                        "max_games_number": int(self.initial_data.get("max_games_number")),
                        "break_between": int(self.initial_data.get("break_between")),
                        "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    }
                )
                bracket = single_el.create_se_bracket()

            elif self.initial_data.get("type") == "DE":
                double_el = DoubleEl(
                    clear_participants(validated_data.get("participants")),
                    {
                        "time_managment": json.loads(self.initial_data.get("time_managment")),
                        "start_time": validated_data.get("start_time"),
                        "avg_game_time": int(self.initial_data.get("avg_game_time")),
                        "max_games_number": int(self.initial_data.get("max_games_number")),
                        "break_between": int(self.initial_data.get("break_between")),
                        "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    },
                )
                bracket = double_el.create_de_bracket()

            elif self.initial_data.get("type") == "RR":
                round_robin = RoundRobin(
                    clear_participants(self.initial_data.get("participants")),
                    {
                        "win": int(self.initial_data.get("points_victory")),
                        "loss": int(self.initial_data.get("points_loss")),
                        "draw": int(self.initial_data.get("points_draw")),
                    },
                    {
                        "time_managment": json.loads(self.initial_data.get("time_managment")),
                        "start_time": validated_data.get("start_time"),
                        "avg_game_time": int(self.initial_data.get("avg_game_time")),
                        "max_games_number": int(self.initial_data.get("max_games_number")),
                        "break_between": int(self.initial_data.get("break_between")),
                        "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    },
                )
                bracket = round_robin.create_round_robin_bracket()

            elif self.initial_data.get("type") == "SW":
                swiss = Swiss(
                    clear_participants(self.initial_data.get("participants")),
                    {
                        "win": int(self.initial_data.get("points_victory")),
                        "loss": int(self.initial_data.get("points_loss")),
                        "draw": int(self.initial_data.get("points_draw")),
                    },
                    {
                        "time_managment": json.loads(self.initial_data.get("time_managment")),
                        "start_time": validated_data.get("start_time"),
                        "avg_game_time": int(self.initial_data.get("avg_game_time")),
                        "max_games_number": int(self.initial_data.get("max_games_number")),
                        "break_between": int(self.initial_data.get("break_between")),
                        "mathes_same_time": int(self.initial_data.get("mathes_same_time")),
                    },
                )
                bracket = swiss.create_swiss_bracket()

            tournament = Tournament.objects.create(
                **validated_data,
                owner=Profile.objects.get(user__email=self.initial_data.get("creater_email")),
            )
            Bracket.objects.create(
                tournament=tournament,
                bracket=bracket,
                type=self.initial_data.get("type"),
            )
        return tournament


class BracketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bracket
        fields = "__all__"

    def create(self, validated_data):
        # initial_data потому что нету в модели Bracket, а передается как дополнительное поле
        if validated_data.get("type") == "SE":
            print(self.initial_data.get("secod_final"))
            single_el = SingleEl(
                clear_participants(self.initial_data.get("participants")),
                {},
                self.initial_data.get("secod_final"),
            )
            bracket = Bracket.objects.create(bracket=single_el.create_se_bracket(), type=validated_data.get("type"))
        elif validated_data.get("type") == "RR":
            round_robin = RoundRobin(
                clear_participants(self.initial_data.get("participants")),
                {
                    "win": int(self.initial_data.get("points_victory")),
                    "loss": int(self.initial_data.get("points_loss")),
                    "draw": int(self.initial_data.get("points_draw")),
                },
            )
            bracket = Bracket.objects.create(
                bracket=round_robin.create_round_robin_bracket(),
                type=validated_data.get("type"),
            )
        elif validated_data.get("type") == "DE":
            double_el = DoubleEl(clear_participants(self.initial_data.get("participants")))
            bracket = Bracket.objects.create(bracket=double_el.create_de_bracket(), type=validated_data.get("type"))
        elif validated_data.get("type") == "SW":
            swiss = Swiss(
                clear_participants(self.initial_data.get("participants")),
                {
                    "win": int(self.initial_data.get("points_victory")),
                    "loss": int(self.initial_data.get("points_loss")),
                    "draw": int(self.initial_data.get("points_draw")),
                },
            )
            bracket = Bracket.objects.create(bracket=swiss.create_swiss_bracket(), type=validated_data.get("type"))

        return bracket

    def update(self, instance, validated_data):
        if not instance.final:
            MultiStage.set_match_score(self.initial_data, instance)
        else:
            if instance.type == "SE":
                SingleEl.set_match_score(self.initial_data, instance.bracket)
            elif instance.type == "RR":
                RoundRobin.set_match_score(self.initial_data, instance.bracket)
            elif instance.type == "DE":
                DoubleEl.set_match_score(self.initial_data, instance.bracket)
            elif instance.type == "SW":
                Swiss.set_match_score(self.initial_data, instance.bracket)

        return super().update(instance, validated_data)


class BracketsField(serializers.RelatedField):
    def to_representation(self, value):
        return {
            "id": value.id,
            "type": value.type,
            "bracket": value.bracket,
        }


class AllBracketSerealizer(serializers.ModelSerializer):
    brackets = BracketsField(many=True, read_only=True)

    class Meta:
        model = Tournament
        fields = ["brackets"]


class GetAllBracketsMPISerializer(serializers.Serializer):
    id = serializers.IntegerField()
    participant_score = serializers.IntegerField()
    participant = serializers.CharField()


class GetAllBracketsMSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    state = serializers.CharField(source="state.name")
    info = GetAllBracketsMPISerializer(many=True)
    start_time = serializers.DateTimeField()


class GetAllBracketsRSerializer(serializers.Serializer):
    serial_number = serializers.IntegerField()
    matches = GetAllBracketsMSerializer(many=True)


class GetAllBracketsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.IntegerField(source="bracket_type.id")
    rounds = GetAllBracketsRSerializer(many=True)
