
import math
import operator
from functools import reduce

from django.db.models import Prefetch, Q

from tournaments.services.auxiliary_services import (
    check_results,
    get_last_top_round,
    get_low_bracket_math_serial_number,
    get_low_bracket_math_serial_number_for_high,
    get_next_math_serial_number,
    is_narrowing_round,
    is_special_low_bracket_round,
    reset_match_participant_info,
    reset_match_participant_info_for_low_bracket,
    reset_match_participant_info_for_low_bracket_from_hight,
    sort_participant_by_score,
    update_match_participant_info,
)

from ..models import (
    Bracket,
    Match,
    MatchParticipantInfo,
    Round,
)


def update_de_bracket(data):
    bracket = Bracket.objects.prefetch_related("se_settings").get(id=data.get("bracket_id"))
    match = Match.objects.select_related("round").prefetch_related("info").get(id=data.get("match_id"))
    print("match id", match.id)
    match_prev_state = match.state.name
    cur_match_state = data.get("state")
    match_results = data.get("match_results")
    advances_to_next = bracket.participant_in_match // 2

    print("match.state", match.state)
    print(match_prev_state, cur_match_state, match.state.id)
    match_cur_round_number = match.round.serial_number
    # Main bracket
    if match_cur_round_number % 2 == 0:
        # P -> S
        if match_prev_state == "PLAYED" and cur_match_state == "SCHEDULED":
            print("P -> S")

            round_cnt = bracket.rounds.count()
            order_by_param = "-id"

            if match_cur_round_number + 2 == get_last_top_round(round_cnt):
                order_by_param = "id"

            if match_cur_round_number + 2 != round_cnt:
                # match_cnt = Match.objects.filter(round__bracket=bracket, round__serial_number=match.round.serial_number).count()
                # обновляем результаты следующего матча верхней сетки
                next_matches_predicates = [Q()]
                cur_serial_number = match.serial_number
                for round_number in range(match_cur_round_number + 2, round_cnt, 2):
                    next_serial_number = get_next_math_serial_number(
                        cur_serial_number, bracket.participant_in_match, advances_to_next
                    )
                    next_matches_predicates.append(
                        Q(Q(round__serial_number=round_number) & Q(serial_number=next_serial_number))
                    )
                    cur_serial_number = next_serial_number

                next_matches = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by(order_by_param))
                ).filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)

                match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                    bracket.participant_in_match
                )
                match_participant_info_r = match_participant_info_l + advances_to_next

                reset_match_participant_info(next_matches, match_participant_info_l, match_participant_info_r)
                next_matches.update(state_id=1)

                # обновляем результаты следующего матча нижней сетки
                next_matches_predicates = [Q()]
                cur_serial_number = match.serial_number
                print("low bracket manupilation")

                low_bracket_round_serial_number = match_cur_round_number + 1

                # Первый раунд нижней сетки
                if low_bracket_round_serial_number == 1:
                    print("first low round")
                    first_low_bracket_matches = Match.objects.prefetch_related(
                        Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                    ).filter(
                        round__serial_number=1,
                        serial_number=get_low_bracket_math_serial_number_for_high(
                            match_cur_round_number,
                            round_cnt,
                            match.serial_number,
                            bracket.participant_in_match,
                            advances_to_next,
                        ),
                        round__bracket=bracket,
                    )
                    match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                        bracket.participant_in_match
                    )
                    match_participant_info_r = match_participant_info_l + advances_to_next
                    reset_match_participant_info(
                        first_low_bracket_matches, match_participant_info_l, match_participant_info_r
                    )
                    first_low_bracket_matches.update(state_id=1)

                # следующий за раундом верхней сетки нижний раунд
                elif not is_narrowing_round(low_bracket_round_serial_number, round_cnt):
                    next_match = Match.objects.prefetch_related(
                        Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                    ).filter(
                        serial_number=get_low_bracket_math_serial_number_for_high(
                            match_cur_round_number,
                            round_cnt,
                            cur_serial_number,
                            bracket.participant_in_match,
                            advances_to_next,
                        ),
                        round__bracket=bracket,
                        round__serial_number=low_bracket_round_serial_number,
                    )
                    match_participant_info_l = 0
                    match_participant_info_r = match_participant_info_l + advances_to_next
                    reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
                    next_match.update(state_id=1)

                # последний раунд нижней сетки
                last_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).filter(serial_number=1, round__bracket=bracket, round__serial_number=round_cnt - 1)
                print("next_match", last_match)
                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next
                reset_match_participant_info(last_match, match_participant_info_l, match_participant_info_r)
                last_match.update(state_id=1)

                #  остальные раунды
                if (
                    round_cnt != low_bracket_round_serial_number + 1
                    and low_bracket_round_serial_number + 1 != get_last_top_round(round_cnt)
                ):
                    print("cicle", low_bracket_round_serial_number)
                    next_matches_predicates = [Q()]
                    is_round_special = []
                    low_serial_number = get_low_bracket_math_serial_number_for_high(
                        match_cur_round_number,
                        round_cnt,
                        cur_serial_number,
                        bracket.participant_in_match,
                        advances_to_next,
                    )
                    cur_serial_number = get_low_bracket_math_serial_number(
                        low_bracket_round_serial_number, round_cnt, low_serial_number, bracket.participant_in_match
                    )

                    # if not is_special_top_bracket_round(low_bracket_round_serial_number-1, round_cnt):
                    #     print('!!cur_serial_number', cur_serial_number)
                    #     cur_serial_number = reflect_number(cur_serial_number, match_cnt)
                    #     print('!!cur_serial_number', cur_serial_number)

                    print("cur_serial_number", cur_serial_number)
                    for round_number in range(low_bracket_round_serial_number + 2, round_cnt, 2):
                        next_matches_predicates.append(
                            Q(Q(round__serial_number=round_number) & Q(serial_number=cur_serial_number))
                        )
                        is_round_special.append(is_narrowing_round(round_number, round_cnt))
                        cur_serial_number = get_low_bracket_math_serial_number(
                            round_number, round_cnt, cur_serial_number, bracket.participant_in_match
                        )
                        # if not is_special_top_bracket_round(round_number-1, round_cnt):
                        #     print('!!!round_number', round_number)
                        #     cur_serial_number = reflect_number(cur_serial_number, match_cnt)

                    next_matches = (
                        Match.objects.prefetch_related(
                            Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                        )
                        .filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)
                        .order_by("-id")
                    )
                    print("next_matches", next_matches)
                    reset_match_participant_info_for_low_bracket_from_hight(
                        next_matches,
                        bracket.participant_in_match,
                        advances_to_next,
                        is_round_special,
                        match.serial_number,
                        round_cnt,
                        low_bracket_round_serial_number,
                    )
                    next_matches.update(state_id=1)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).filter(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next
                reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
                next_match.update(state_id=1)

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
            order_by_param = "-id"

            if match_cur_round_number + 2 == get_last_top_round(round_cnt):
                order_by_param = "id"

            if (
                not check_results(match_prev_res, list(map(int, match_cur_res)))
                and match_cur_round_number + 2 != round_cnt
            ):
                # обновляем результаты следующего матча верхней сетки
                next_matches_predicates = [Q()]
                cur_serial_number = match.serial_number
                for round_number in range(match_cur_round_number + 2, round_cnt, 2):
                    next_serial_number = get_next_math_serial_number(
                        cur_serial_number, bracket.participant_in_match, advances_to_next
                    )
                    next_matches_predicates.append(
                        Q(Q(round__serial_number=round_number) & Q(serial_number=next_serial_number))
                    )
                    cur_serial_number = next_serial_number

                next_matches = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by(order_by_param))
                ).filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)

                match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                    bracket.participant_in_match
                )
                match_participant_info_r = match_participant_info_l + advances_to_next

                reset_match_participant_info(next_matches, match_participant_info_l, match_participant_info_r)
                next_matches.update(state_id=1)

                # обновляем результаты следующего матча нижней сетки
                next_matches_predicates = [Q()]
                cur_serial_number = match.serial_number
                print("low bracket manupilation")

                low_bracket_round_serial_number = match_cur_round_number + 1

                # Первый раунд нижней сетки
                if low_bracket_round_serial_number == 1:
                    print("first low round")
                    first_low_bracket_matches = Match.objects.prefetch_related(
                        Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                    ).filter(
                        round__serial_number=1,
                        serial_number=get_low_bracket_math_serial_number_for_high(
                            match_cur_round_number,
                            round_cnt,
                            match.serial_number,
                            bracket.participant_in_match,
                            advances_to_next,
                        ),
                        round__bracket=bracket,
                    )
                    match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                        bracket.participant_in_match
                    )
                    match_participant_info_r = match_participant_info_l + advances_to_next
                    reset_match_participant_info(
                        first_low_bracket_matches, match_participant_info_l, match_participant_info_r
                    )
                    first_low_bracket_matches.update(state_id=1)

                # следующий за раундом верхней сетки нижний раунд
                elif not is_narrowing_round(low_bracket_round_serial_number, round_cnt):
                    next_match = Match.objects.prefetch_related(
                        Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                    ).filter(
                        serial_number=get_low_bracket_math_serial_number_for_high(
                            match_cur_round_number,
                            round_cnt,
                            cur_serial_number,
                            bracket.participant_in_match,
                            advances_to_next,
                        ),
                        round__bracket=bracket,
                        round__serial_number=low_bracket_round_serial_number,
                    )
                    match_participant_info_l = 0
                    match_participant_info_r = match_participant_info_l + advances_to_next
                    reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
                    next_match.update(state_id=1)

                # последний раунд нижней сетки
                # if low_bracket_round_serial_number + 1 != get_last_top_round(round_cnt):
                last_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).filter(serial_number=1, round__bracket=bracket, round__serial_number=round_cnt - 1)
                print("next_match", last_match)
                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next
                reset_match_participant_info(last_match, match_participant_info_l, match_participant_info_r)
                last_match.update(state_id=1)

                #  остальные раунды
                if (
                    round_cnt != low_bracket_round_serial_number + 1
                    and match_cur_round_number + 2 != get_last_top_round(round_cnt)
                ):
                    print("cicle", low_bracket_round_serial_number)
                    next_matches_predicates = [Q()]
                    is_round_special = []
                    low_serial_number = get_low_bracket_math_serial_number_for_high(
                        match_cur_round_number,
                        round_cnt,
                        cur_serial_number,
                        bracket.participant_in_match,
                        advances_to_next,
                    )
                    cur_serial_number = get_low_bracket_math_serial_number(
                        low_bracket_round_serial_number, round_cnt, low_serial_number, bracket.participant_in_match
                    )

                    print("cur_serial_number", cur_serial_number)
                    for round_number in range(low_bracket_round_serial_number + 2, round_cnt, 2):
                        next_matches_predicates.append(
                            Q(Q(round__serial_number=round_number) & Q(serial_number=cur_serial_number))
                        )
                        is_round_special.append(is_narrowing_round(round_number, round_cnt))
                        next_serial_number = get_low_bracket_math_serial_number(
                            round_number, round_cnt, cur_serial_number, bracket.participant_in_match
                        )
                        cur_serial_number = next_serial_number

                    next_matches = (
                        Match.objects.prefetch_related(
                            Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                        )
                        .filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)
                        .order_by("-id")
                    )
                    print("next_matches", next_matches)
                    reset_match_participant_info_for_low_bracket_from_hight(
                        next_matches,
                        bracket.participant_in_match,
                        advances_to_next,
                        is_round_special,
                        match.serial_number,
                        round_cnt,
                        low_bracket_round_serial_number,
                    )
                    next_matches.update(state_id=1)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).filter(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next
                reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
                next_match.update(state_id=1)

            # обновляем результаты текущего матча
            update_match_participant_info(match_results, match.info.all())
            if match_cur_round_number + 2 != round_cnt:
                # обновляем результаты следующего матча верхней сетки
                sorted_participant_ids = sort_participant_by_score(match_results)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by(order_by_param))
                ).get(
                    serial_number=get_next_math_serial_number(
                        match.serial_number, bracket.participant_in_match, advances_to_next
                    ),
                    round__bracket=bracket,
                    round__serial_number=match.round.serial_number + 2,
                )

                match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                    bracket.participant_in_match
                )
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())

                # обновляем результаты следующего матча нижней сетки
                sorted_participant_ids = sort_participant_by_score(match_results, False)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(
                    serial_number=get_low_bracket_math_serial_number_for_high(
                        match_cur_round_number,
                        round_cnt,
                        match.serial_number,
                        bracket.participant_in_match,
                        advances_to_next,
                    ),
                    round__bracket=bracket,
                    # check for prelast match in top bracket
                    round__serial_number=match.round.serial_number
                    + (1 if match_cur_round_number != round_cnt - 4 else 3),
                )

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())

            match.state_id = 2
            match.save()
        # S -> P
        elif match_prev_state == "SCHEDULED" and cur_match_state == "PLAYED":
            # обновляем результаты текущего матча
            update_match_participant_info(match_results, match.info.all())

            round_cnt = bracket.rounds.count()
            # match_cnt = Match.objects.filter(
            #     round__bracket=bracket, round__serial_number=match.round.serial_number
            # ).count()
            match_cur_round_number = match.round.serial_number

            order_by_param = "-id"

            print("match_cur_round_number", match_cur_round_number)
            print("get_last_top_round(round_cnt)", get_last_top_round(round_cnt))

            if match_cur_round_number + 2 == get_last_top_round(round_cnt):
                order_by_param = "id"

            if match_cur_round_number + 2 != round_cnt:
                # обновляем результаты следующего матча верхней сетки
                sorted_participant_ids = sort_participant_by_score(match_results)
                print(
                    "match serial number",
                    get_next_math_serial_number(match.serial_number, bracket.participant_in_match, advances_to_next),
                )
                print("match.round.serial_number", match.round.serial_number)
                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by(order_by_param))
                ).get(
                    serial_number=get_next_math_serial_number(
                        match.serial_number, bracket.participant_in_match, advances_to_next
                    ),
                    round__bracket=bracket,
                    round__serial_number=match.round.serial_number + 2,
                )
                print("next_match", next_match)
                match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                    bracket.participant_in_match
                )
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())

                # обновляем результаты следующего матча нижней сетки
                sorted_participant_ids = sort_participant_by_score(match_results, False)
                print("low bracket")
                next_match_serial_number = get_low_bracket_math_serial_number_for_high(
                    match_cur_round_number,
                    round_cnt,
                    match.serial_number,
                    bracket.participant_in_match,
                    advances_to_next,
                )

                # if is_special_top_bracket_round(match_cur_round_number, round_cnt):
                #     next_match_serial_number = reflect_number(next_match_serial_number, match_cnt)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(
                    serial_number=next_match_serial_number,
                    round__bracket=bracket,
                    # check for prelast match in top bracket
                    round__serial_number=match.round.serial_number
                    + (1 if match_cur_round_number != round_cnt - 4 else 3),
                )

                if match_cur_round_number == 0:
                    match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                        bracket.participant_in_match
                    )
                else:
                    match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())

            match.state_id = 2
            match.save()
        # S -> S
        else:
            match.state_id = 1
            match.save()
            # elif match_prev_state == "SCHEDULED" and cur_match_state == "SCHEDULED":
            update_match_participant_info(match_results, match.info.all())
    else:
        # P -> S
        if match_prev_state == "PLAYED" and cur_match_state == "SCHEDULED":
            print("P -> S")
            round_cnt = bracket.rounds.count()
            match_cur_round_number = match.round.serial_number

            if round_cnt != match_cur_round_number + 1:
                next_matches_predicates = [Q()]
                is_round_special = []
                cur_serial_number = get_low_bracket_math_serial_number(
                    match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                )
                for round_number in range(match_cur_round_number + 2, round_cnt, 2):
                    next_matches_predicates.append(
                        Q(Q(round__serial_number=round_number) & Q(serial_number=cur_serial_number))
                    )
                    is_round_special.append(is_narrowing_round(round_number, round_cnt))
                    next_serial_number = get_low_bracket_math_serial_number(
                        round_number, round_cnt, cur_serial_number, bracket.participant_in_match
                    )
                    cur_serial_number = next_serial_number

                next_matches = (
                    Match.objects.prefetch_related(
                        Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                    )
                    .filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)
                    .order_by("-id")
                )
                reset_match_participant_info_for_low_bracket(
                    next_matches, bracket.participant_in_match, advances_to_next, is_round_special, match.serial_number
                )
                next_matches.update(state_id=1)

            next_match = Match.objects.prefetch_related(
                Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
            ).filter(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))

            match_participant_info_l = 0
            match_participant_info_r = match_participant_info_l + advances_to_next
            reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
            next_match.update(state_id=1)

            # обновляем результаты текущего матча
            update_match_participant_info(match_results, match.info.all())
            match.state_id = 1
            match.save()

        # P -> P
        elif match_prev_state == "PLAYED" and cur_match_state == "PLAYED":
            print("P -> P")
            match_prev_res = match.info.order_by("-participant_score").values_list("id", flat=True)
            match_cur_res = sort_participant_by_score(match_results)

            round_cnt = bracket.rounds.count()
            match_cur_round_number = match.round.serial_number

            if not check_results(match_prev_res, list(map(int, match_cur_res))):
                if round_cnt != match_cur_round_number + 1:
                    next_matches_predicates = [Q()]
                    is_round_special = []
                    cur_serial_number = get_low_bracket_math_serial_number(
                        match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                    )
                    for round_number in range(match_cur_round_number + 2, round_cnt, 2):
                        next_matches_predicates.append(
                            Q(Q(round__serial_number=round_number) & Q(serial_number=cur_serial_number))
                        )
                        is_round_special.append(is_narrowing_round(round_number, round_cnt))
                        next_serial_number = get_low_bracket_math_serial_number(
                            round_number, round_cnt, cur_serial_number, bracket.participant_in_match
                        )
                        cur_serial_number = next_serial_number

                    next_matches = (
                        Match.objects.prefetch_related(
                            Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                        )
                        .filter(reduce(operator.or_, next_matches_predicates), round__bracket=bracket)
                        .order_by("-id")
                    )
                    reset_match_participant_info_for_low_bracket(
                        next_matches,
                        bracket.participant_in_match,
                        advances_to_next,
                        is_round_special,
                        match.serial_number,
                    )
                    next_matches.update(state_id=1)

                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).filter(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next
                reset_match_participant_info(next_match, match_participant_info_l, match_participant_info_r)
                next_match.update(state_id=1)

            # обновляем результаты текущего матча
            update_match_participant_info(match_results, match.info.all())
            if match_cur_round_number + 1 == round_cnt or (match_cur_round_number + 2 == round_cnt and round_cnt == 5):
                sorted_participant_ids = sort_participant_by_score(match_results)
                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))
                print("next_match", next_match)

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())
            elif match_cur_round_number + 1 != round_cnt:
                print("here")
                # обновляем результаты следующего матча
                sorted_participant_ids = sort_participant_by_score(match_results)
                print(
                    "match number",
                    get_low_bracket_math_serial_number(
                        match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                    ),
                )
                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(
                    serial_number=get_low_bracket_math_serial_number(
                        match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                    ),
                    round__bracket=bracket,
                    round__serial_number=match.round.serial_number + 2,
                )

                if is_special_low_bracket_round(match_cur_round_number, round_cnt):
                    match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                        bracket.participant_in_match
                    )
                else:
                    match_participant_info_l = advances_to_next
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )
                update_match_participant_info(next_match_results, next_match.info.all())

            match.state_id = 2
            match.save()
        # S -> P
        elif match_prev_state == "SCHEDULED" and cur_match_state == "PLAYED":
            # обновляем результаты текущего матча
            update_match_participant_info(match_results, match.info.all())
            round_cnt = bracket.rounds.count()
            match_cur_round_number = match.round.serial_number
            print("match_cur_round_number", match_cur_round_number)
            if match_cur_round_number + 1 == round_cnt or (match_cur_round_number + 2 == round_cnt and round_cnt == 5):
                sorted_participant_ids = sort_participant_by_score(match_results)
                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(serial_number=1, round__bracket=bracket, round__serial_number=get_last_top_round(round_cnt))
                print("next_match", next_match)

                match_participant_info_l = 0
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())
            elif match_cur_round_number + 1 != round_cnt:
                print("here")
                # обновляем результаты следующего матча
                sorted_participant_ids = sort_participant_by_score(match_results)
                print(
                    "match number",
                    get_low_bracket_math_serial_number(
                        match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                    ),
                )
                next_match = Match.objects.prefetch_related(
                    Prefetch("info", queryset=MatchParticipantInfo.objects.all().order_by("-id"))
                ).get(
                    serial_number=get_low_bracket_math_serial_number(
                        match_cur_round_number, round_cnt, match.serial_number, bracket.participant_in_match
                    ),
                    round__bracket=bracket,
                    round__serial_number=match.round.serial_number + 2,
                )

                if is_special_low_bracket_round(match_cur_round_number, round_cnt):
                    match_participant_info_l = ((match.serial_number - 1) * advances_to_next) % (
                        bracket.participant_in_match
                    )
                else:
                    match_participant_info_l = advances_to_next
                match_participant_info_r = match_participant_info_l + advances_to_next

                next_match_info_ids = [f"{id}" for id in next_match.info.values_list("id", flat=True)]

                next_match_results = dict(
                    zip(
                        next_match_info_ids[match_participant_info_l:match_participant_info_r][::-1],
                        [
                            {"participant": match_results.get(sorted_participant_ids[i]).get("participant"), "score": 0}
                            for i in range(advances_to_next)
                        ],
                    )
                )

                update_match_participant_info(next_match_results, next_match.info.all())
            # последний матч нижней сетки

            match.state_id = 2
            match.save()

        # S -> S
        else:
            match.state_id = 1
            match.save()
            update_match_participant_info(match_results, match.info.all())


def create_de_bracket(bracket: Bracket, participants: list):
    # log(player_in_match)total_players -  total number of rounds in the tournament
    p_in_m = bracket.participant_in_match
    participants_cnt = len(participants)

    next_round_p = p_in_m // 2
    print()

    number_of_rounds_w = math.ceil(math.log(len(participants) // next_round_p, 2)) + 1
    number_of_rounds_l = (math.ceil(math.log(len(participants) // next_round_p, 2)) - 1) * 2

    print("participants", participants, len(participants))
    print("number_of_rounds_w", number_of_rounds_w)
    print("number_of_rounds_l", number_of_rounds_l)

    missing_participant_cnt = ((p_in_m) ** (number_of_rounds_w - 1)) // (p_in_m // 2) - participants_cnt

    print("missing_participant_cnt", missing_participant_cnt)

    if missing_participant_cnt > 0:
        for _ in range(missing_participant_cnt):
            participants.append("---")

    print("participants", participants)

    _number_of_rounds_l = number_of_rounds_l
    l_start = 1
    while _number_of_rounds_l != 1:
        l_start += 2
        _number_of_rounds_l -= 1

    _number_of_rounds_w = number_of_rounds_w
    w_start = 0
    while _number_of_rounds_w != 1:
        w_start += 2
        _number_of_rounds_w -= 1

    unsaved_matches = []
    matches_info = []

    rounds_l = []
    rounds_w = []

    # Создаем раунды  для нижней сетки, номера нечетные
    for number in range(l_start, -1, -2):
        rounds_l.append(Round(bracket=bracket, serial_number=number))

    # Создаем раунды для верхней сетки, номера четные
    for number in range(w_start, -1, -2):
        rounds_w.append(Round(bracket=bracket, serial_number=number))

    Round.objects.bulk_create(rounds_l + rounds_w)

    number_of_match_in_round_l = 1
    match_serial_number_cnt = 0
    flag_l = False

    # Заполняем нижнию сетку с последнего по первый
    for r in range(number_of_rounds_l):
        match_serial_number_cnt = number_of_match_in_round_l
        for _ in range(number_of_match_in_round_l):
            match = Match(round=rounds_l[r], serial_number=match_serial_number_cnt, state_id=1)
            unsaved_matches.append(match)
            for _ in range(bracket.participant_in_match):
                matches_info.append(MatchParticipantInfo(match=match, participant_score=0, participant="---"))
            # Уменьшаем серийный номер матча
            match_serial_number_cnt = match_serial_number_cnt - 1

        if flag_l:
            # Увеличиваем количество матчей раунде
            number_of_match_in_round_l = number_of_match_in_round_l * 2
            flag_l = False
        else:
            flag_l = True

    number_of_match_in_round_w = 1
    match_serial_number_cnt = len(participants)
    flag_l = False

    # Заполняем верхнию сетку с последнего по первый
    for r in range(number_of_rounds_w):
        match_serial_number_cnt = number_of_match_in_round_w
        for m in range(number_of_match_in_round_w):
            match = Match(round=rounds_w[r], serial_number=match_serial_number_cnt, state_id=1)
            unsaved_matches.append(match)
            # Для первого
            if r == number_of_rounds_w - 1:
                for p in range(bracket.participant_in_match):
                    matches_info.append(
                        MatchParticipantInfo(
                            match=match,
                            participant_score=0,
                            participant=participants[m * p_in_m + p],
                        )
                    )
            # Для остальных
            else:
                for _ in range(bracket.participant_in_match):
                    matches_info.append(MatchParticipantInfo(match=match, participant_score=0, participant="---"))
            # Уменьшаем серийный номер матча
            match_serial_number_cnt = match_serial_number_cnt - 1

        # Увеличиваем количество матчей раунде
        if flag_l:
            number_of_match_in_round_w = number_of_match_in_round_w * 2
        else:
            flag_l = True

    Match.objects.bulk_create(unsaved_matches)
    MatchParticipantInfo.objects.bulk_create(matches_info)
