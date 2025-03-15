import operator
from functools import reduce

from django.db.models import Prefetch, Q

from tournaments.services.auxiliary_services import (
    check_results,
    get_next_math_serial_number,
    reset_match_participant_info,
    sort_participant_by_score,
    update_match_participant_info,
)

from ..models import (
    Bracket,
    Match,
    MatchParticipantInfo,
    Round,
    SEBracketSettings,
)


def create_se_bracket(bracket: Bracket, participants: list, settings: SEBracketSettings) -> None:
    p_cnt = len(participants)
    # p_in_m work from 2 to 8
    p_in_m = bracket.participant_in_match
    # next_round_p work from 1 to 4
    next_round_p = settings.advances_to_next
    # коэффицент показывающий отношение выбывших и прошедших участников в одном матче
    multiplicity_factor = p_in_m / next_round_p

    number_of_rounds = 1
    remaining_p_cnt = p_cnt
    # O(log(n))
    while remaining_p_cnt > p_in_m:
        print("remaining_p_cnt", remaining_p_cnt)
        number_of_rounds = number_of_rounds + 1
        remaining_p_cnt = remaining_p_cnt / multiplicity_factor

    # if next_round_p != 1:
    #     number_of_rounds = 1
    #     remaining_p_cnt = p_cnt
    #     while remaining_p_cnt > p_in_m:
    #         number_of_rounds = number_of_rounds + 1
    #         remaining_p_cnt = remaining_p_cnt / multiplicity_factor
    # else:
    #     # для next_round_p = 1
    #     number_of_rounds = math.ceil(math.log(p_cnt, p_in_m))
    #     print('number_of_rounds old', number_of_rounds)
    # number_of_match_in_round = bracket.participant_in_match**(number_of_rounds-1)

    number_of_match_in_round = 1

    print("p_in_m", p_in_m)
    print("next_round_p", next_round_p)
    print("participants", participants)
    print("number_of_rounds", number_of_rounds)
    print("number_of_match_in_round", number_of_match_in_round)

    rounds = []
    unsaved_matches = []
    matches_info = []

    # Не правильно работает дополнение для next_round_p > 1
    # print('participant count', (p_in_m**number_of_rounds) // next_round_p)
    missing_p_cnt = ((p_in_m**number_of_rounds) // next_round_p) - p_cnt
    # missing_p_cnt = ((p_in_m // next_round_p) ** (number_of_rounds ))  - p_cnt

    print("missing_participant_cnt", missing_p_cnt)

    # Добавить диаграмму
    if missing_p_cnt > 0:
        where_insert_cnt = p_cnt // 2
        for _ in range(missing_p_cnt):  # O(n)
            participants.insert(where_insert_cnt, "---")
            where_insert_cnt = where_insert_cnt + 1

    print("participants", participants)

    # match_cnt_in_round = 1

    # for r in range(number_of_rounds-1):
    #     match_cnt_in_round = match_cnt_in_round * (p_in_m // next_round_p)
    #     match_serial_number_cnt =  match_serial_number_cnt + match_cnt_in_round

    # print("match_serial_number_sum", match_serial_number_cnt)

    # Создаем раунды O(log(n))
    for number in range(number_of_rounds - 1, -1, -1):
        rounds.append(Round(bracket=bracket, serial_number=number))
    Round.objects.bulk_create(rounds)

    # Заполняем раунды матчами с последнего по первый O(nlog(n))
    for r in range(number_of_rounds):  # O(log(n))
        match_serial_number_cnt = number_of_match_in_round
        for m in range(number_of_match_in_round):  # O(n)
            match = Match(round=rounds[r], serial_number=match_serial_number_cnt, state_id=1)
            unsaved_matches.append(match)
            # Для первого
            if r == number_of_rounds - 1:
                for p in range(p_in_m):
                    print("m*p_in_m+p", m * p_in_m + p)
                    matches_info.append(
                        MatchParticipantInfo(
                            match=match,
                            participant_score=0,
                            participant=participants[m * p_in_m + p],
                        )
                    )
            # Для остальных
            else:
                for _ in range(p_in_m):
                    matches_info.append(MatchParticipantInfo(match=match, participant_score=0, participant="---"))
            # Уменьшаем серийный номер матча
            match_serial_number_cnt = match_serial_number_cnt - 1
        # Увеличиваем количество матчей раунде
        number_of_match_in_round = number_of_match_in_round * (p_in_m // next_round_p)
        # Сохраняем матчи

    Match.objects.bulk_create(unsaved_matches)
    MatchParticipantInfo.objects.bulk_create(matches_info)


def update_se_bracket(data):
    print("data", data)
    bracket = Bracket.objects.prefetch_related("se_settings").get(id=data.get("bracket_id"))
    match = Match.objects.select_related("round").prefetch_related("info").get(id=data.get("match_id"))
    print("match id", match.id)
    match_prev_state = match.state.name
    cur_match_state = data.get("state")
    match_results = data.get("match_results")
    advances_to_next = bracket.se_settings.first().advances_to_next

    print("match.state", match.state)
    print(match_prev_state, cur_match_state, match.state.id)

    match.start_time = data.get("start_time")

    # P -> S
    if match_prev_state == "PLAYED" and cur_match_state == "SCHEDULED":
        print("P -> S")

        round_cnt = bracket.rounds.count()
        match_cur_round_number = match.round.serial_number

        print("match_cur_round_number", match_cur_round_number)
        print("round_cnt", round_cnt)

        if match_cur_round_number + 1 != round_cnt:
            next_matches_predicates = [Q()]
            cur_serial_number = match.serial_number
            for round_number in range(match_cur_round_number + 1, round_cnt):
                next_serial_number = get_next_math_serial_number(
                    cur_serial_number, bracket.participant_in_match, advances_to_next
                )
                next_matches_predicates.append(
                    Q(Q(round__serial_number=round_number) & Q(serial_number=next_serial_number))
                )
                cur_serial_number = next_serial_number

            next_matches = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
            ).filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)

            print("round_cnt", round_cnt)
            print("match_cur_round_number", match_cur_round_number)
            print("next_matches_predicates", next_matches_predicates)
            print("next_matches", next_matches)

            match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (bracket.participant_in_match)
            match_participant_info_r = match_participant_info_l + advances_to_next

            print("match_participant_info_l", match_participant_info_l)
            print("match_participant_info_r", match_participant_info_r)

            reset_match_participant_info(next_matches, match_participant_info_l, match_participant_info_r)
            next_matches.update(state_id=1)

        # обновляем результаты текущего матча
        update_match_participant_info(match_results, match.info.all())
        match.state_id = 1
        match.save()

    # P -> P
    elif match_prev_state == "PLAYED" and cur_match_state == "PLAYED":
        print("P -> P")
        match_prev_res = match.info.order_by("-participant_score").values_list("id", flat=True)
        match_cur_res = sort_participant_by_score(match_results)

        print("match_prev_res", match_prev_res)
        print("match_cur_res", match_cur_res)

        round_cnt = bracket.rounds.count()
        match_cur_round_number = match.round.serial_number

        if (
            not check_results(match_prev_res, list(map(int, match_cur_res)))
            and round_cnt != match_cur_round_number + 2
            and match_cur_round_number + 1 != round_cnt
        ):
            next_matches_predicates = [Q()]
            cur_serial_number = get_next_math_serial_number(
                match.serial_number, bracket.participant_in_match, advances_to_next
            )
            for round_number in range(match_cur_round_number + 2, round_cnt):
                next_serial_number = get_next_math_serial_number(
                    cur_serial_number, bracket.participant_in_match, advances_to_next
                )
                next_matches_predicates.append(
                    Q(Q(round__serial_number=round_number) & Q(serial_number=next_serial_number))
                )
                cur_serial_number = next_serial_number

            next_matches = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
            ).filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)

            print("round_cnt", round_cnt)
            print("match_cur_round_number", match_cur_round_number)
            print("next_match_numbers", next_matches_predicates)
            print("next_matches", next_matches)

            match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (bracket.participant_in_match)
            match_participant_info_r = match_participant_info_l + advances_to_next

            reset_match_participant_info(next_matches, match_participant_info_l, match_participant_info_r)
            next_matches.update(state_id=1)

        # обновляем результаты текущего матча
        update_match_participant_info(match_results, match.info.all())
        if match_cur_round_number + 1 != round_cnt:
            # обновляем результаты следующего матча
            sorted_participant_ids = sort_participant_by_score(match_results)
            next_match = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
            ).get(
                serial_number=get_next_math_serial_number(
                    match.serial_number, bracket.participant_in_match, advances_to_next
                ),
                round__bracket=bracket,
                round__serial_number=match.round.serial_number + 1,
            )

            match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (bracket.participant_in_match)
            match_participant_info_r = match_participant_info_l + advances_to_next

            next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

            print("match_participant_info_l", match_participant_info_l)
            print("match_participant_info_r", match_participant_info_r)

            next_match_results = dict(
                zip(
                    next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                    [
                        {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                        for i in range(advances_to_next)
                    ],
                )
            )

            print("next_match_results", next_match_results)
            print("next_match_info_ids", next_match_info_ids)

            update_match_participant_info(next_match_results, next_match.info.all())

            print("next_match", next_match)
            print("sorted_participant_ids", sorted_participant_ids)

        match.state_id = 2
        match.save()
    # S -> P
    elif match_prev_state == "SCHEDULED" and cur_match_state == "PLAYED":
        # обновляем результаты текущего матча
        update_match_participant_info(match_results, match.info.all())

        round_cnt = bracket.rounds.count()
        match_cur_round_number = match.round.serial_number

        if match_cur_round_number + 1 != round_cnt:
            # обновляем результаты следующего матча
            sorted_participant_ids = sort_participant_by_score(match_results)
            next_match = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
            ).get(
                serial_number=get_next_math_serial_number(
                    match.serial_number, bracket.participant_in_match, advances_to_next
                ),
                round__bracket=bracket,
                round__serial_number=match.round.serial_number + 1,
            )

            print("match.serial_number-1", match.serial_number - advances_to_next)
            match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (bracket.participant_in_match)
            match_participant_info_r = match_participant_info_l + advances_to_next

            next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

            print("match_participant_info_l", match_participant_info_l)
            print("match_participant_info_r", match_participant_info_r)

            next_match_results = dict(
                zip(
                    next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                    [
                        {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                        for i in range(advances_to_next)
                    ],
                )
            )

            print("next_match_results", next_match_results)
            print("next_match_info_ids", next_match_info_ids)

            update_match_participant_info(next_match_results, next_match.info.all())

            print("next_match", next_match)
            print("sorted_participant_ids", sorted_participant_ids)

        match.state_id = 2
        match.save()
    # S -> S
    else:
        match.state_id = 1
        match.save()
        # elif match_prev_state == "SCHEDULED" and cur_match_state == "SCHEDULED":
        update_match_participant_info(match_results, match.info.all())
