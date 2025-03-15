
import math

from django.db.models import Count, F, Prefetch, Q

from tournaments.orm_functions import JsonGroupArray
from tournaments.services.auxiliary_services import set_match_participant_info, set_match_participant_results

from ..models import (
    Bracket,
    Match,
    MatchParticipantInfo,
    Round,
)


def create_sw_bracket(bracket: Bracket, participants: list, number_of_rounds: int | None):
    participants_cnt = len(participants)
    p_in_m = bracket.participant_in_match

    if number_of_rounds is None:
        number_of_rounds = math.ceil(math.log(participants_cnt, p_in_m))

    # missing_participant_cnt = p_in_m - (participants_cnt % p_in_m)
    # print('missing_participant_cnt', missing_participant_cnt)

    if participants_cnt % p_in_m > 0:
        for _ in range(p_in_m - (participants_cnt % p_in_m)):
            participants.append("---")

    match_serial_number_cnt = 0
    number_of_match_in_round = math.ceil(participants_cnt / p_in_m)

    # if participants_cnt % 2 == 1:
    #     participants = participants + ['---']

    # O(log(n))
    for i in range(number_of_rounds):
        _round = Round.objects.creeate(bracket=bracket, serial_number=i)
        # O(n / 2)
        for m in range(number_of_match_in_round):
            match = Match.objects.create(round=_round, serial_number=match_serial_number_cnt, state_id=1)
            if i == 0:
                for p in range(p_in_m):
                    print("m*p_in_m+p", m * p_in_m + p)
                    MatchParticipantInfo.objects.create(
                            match=match,
                            participant_score=0,
                            participant=participants[m * p_in_m + p],
                        )
            else:
                for _ in range(p_in_m):
                    MatchParticipantInfo.objects.create(match=match, participant_score=0, participant="TBO")

            match_serial_number_cnt = match_serial_number_cnt + 1


def update_sw_bracket(data):
    print("data", data)
    bracket = Bracket.objects.prefetch_related("sw_settings").get(id=data.get("bracket_id"))
    match = Match.objects.select_related("round").prefetch_related("info").get(id=data.get("match_id"))
    print("match id", match.id)
    match_prev_state = match.state.name
    cur_match_state = data.get("state")
    match_results = data.get("match_results")
    settings = bracket.sw_settings.first()

    print("match.state", match.state)
    print(match_prev_state, cur_match_state, match.state.id)
    set_match_participant_results(match_results, match.info.all())
    # S
    if cur_match_state == "SCHEDULED":
        match.state_id = 1
    # P
    else:
        match.state_id = 2
    match.save()
    # update_match_participant_info(match_results, match.info.all())

    # max_value = MatchParticipantInfo.objects.filter(match_id=OuterRef("match_id")).annotate(max_participant_score=Max('participant_score')).order_by('-max_participant_score').values('max_participant_score')

    # print(MatchParticipantInfo.objects.annotate(max_participant_score=Max('participant_score')).filter(match_id=1216, participant_score=Subquery(max_value)).values('participant_score'))
    # print(MatchParticipantInfo.objects.annotate(max_participant_score=Max('participant_score')).filter(match_id=1216, participant_score=F('max_participant_score')).values('participant_score').query)

    # winner = MatchParticipantInfo.objects.filter(
    #         participant_score=Subquery(max_value),
    #         match=OuterRef("pk"),
    #     ).annotate(
    #         winner_count=Count('participant_score')
    #     ).values('participant')

    # print(Match.objects.filter(Q(round__bracket=bracket), state_id=2).annotate(winner=Subquery(winner)).values_list('winner', flat=True))
    # print(Match.objects.filter(Q(round__bracket=bracket), state_id=2).annotate(winner=Subquery(winner)).query)

    bracket_result = (
        MatchParticipantInfo.objects.filter(Q(match__round__bracket=bracket), ~Q(participant="TBO"))
        .values("participant")
        .annotate(
            win=Count("participant_result", filter=Q(participant_result__id=2)),
            loss=Count("participant_result", filter=Q(participant_result__id=3)),
            draw=Count("participant_result", filter=Q(participant_result__id=4)),
            play_with=JsonGroupArray("participant", distinct=True),
            total=F("win") * settings.points_per_victory
            + F("loss") * settings.points_per_loss
            + F("draw") * settings.points_per_draw,
        )
    )

    print("bracket_result", bracket_result)

    # Все матчи в раунде сыграны
    if not Match.objects.filter(round__bracket=bracket, round=match.round, state_id=1).exists():
        bracket_result = sorted(bracket_result, key=lambda x: x.get("total"), reverse=True)

        print("bracket_result", bracket_result)

        next_round = [{"participant": p.get("participant"), "score": 0} for p in bracket_result]

        print("next_round", next_round)
        round_cnt = bracket.rounds.count()
        next_round_serial_number = match.round.serial_number + 1
        if next_round_serial_number != round_cnt:
            next_matches = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("id"))
            ).filter(round__bracket=bracket, round__serial_number=next_round_serial_number)
            for index, match in enumerate(next_matches):
                set_match_participant_info(
                    next_round[
                        index * bracket.participant_in_match : index * bracket.participant_in_match
                        + bracket.participant_in_match
                    ],
                    match.info.all(),
                )

            # MatchParticipantInfo.objects.filter(match__round__bracket=bracket).values('participant').annotate(
            #     Count('participant_result', filter=Q(participant_result__id=2))
            # )

        # for m in range(math.ceil(participants_cnt / p_in_m)):
        #     match = Match(
        #         round=_round, serial_number=match_serial_number_cnt, state_id=1
        #     )
        #     unsaved_matches.append(match)
        #     if i == 0:
        #         for p in range(p_in_m):
        #             print("m*p_in_m+p", m * p_in_m + p)
        #             matches_info.append(
        #                 MatchParticipantInfo(
        #                     match=match,
        #                     participant_score=0,
        #                     participant=participants[m * p_in_m + p],
        #                 )
        #             )
        #     else:
        #         for _ in range(p_in_m):
        #             matches_info.append(
        #                 MatchParticipantInfo(
        #                     match=match, participant_score=0, participant="TBO"
        #                 )
        #             )
