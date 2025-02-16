import math

from django.db.models.query import QuerySet

from ..models import (
    Match,
    MatchParticipantInfo,
)


def set_match_participant_info(match_results: dict, info: QuerySet[MatchParticipantInfo]):
    for index, i in enumerate(info):
        i.participant_score = match_results[index].get("score")
        i.participant = match_results[index].get("participant")
    MatchParticipantInfo.objects.bulk_update(info, ["participant_score", "participant"])


def update_match_participant_info(match_results: dict, info: QuerySet[MatchParticipantInfo]):
    for i in info:
        match_result = match_results.get(f"{i.id}")
        if match_result is not None:
            i.participant_score = match_result.get("score")
            i.participant = match_result.get("participant")
            i.participant_result_id = match_result.get("participant_result", 1)

    MatchParticipantInfo.objects.bulk_update(info, ["participant_score", "participant", "participant_result_id"])


def reset_match_participant_info(mathes: QuerySet[Match], left_border: int, right_border: int):
    info = []
    for m in mathes:
        for i in m.info.all()[left_border:right_border]:
            i.participant_score = 0
            i.participant = "---"
            info.append(i)

    MatchParticipantInfo.objects.bulk_update(info, ["participant_score", "participant"])


def reset_match_participant_info_for_low_bracket(
    mathes: QuerySet[Match], p_i_m: int, advances_to_next: int, is_special: list[bool], prev_serial_number: int
) -> None:
    info = []
    prev_math_serial_number = prev_serial_number
    for i, m in enumerate(mathes):
        print("match id", m.id)
        if is_special[i]:
            print("special")
            match_participant_info_l = ((prev_math_serial_number - 1) * advances_to_next) % (p_i_m)
        else:
            match_participant_info_l = advances_to_next
        print("prev_math_serial_number", prev_math_serial_number)
        print("match_participant_info_l", match_participant_info_l)
        match_participant_info_r = match_participant_info_l + advances_to_next
        for i in m.info.all()[match_participant_info_l:match_participant_info_r]:
            i.participant_score = 0
            i.participant = "---"
            info.append(i)
        prev_math_serial_number = m.serial_number

    MatchParticipantInfo.objects.bulk_update(info, ["participant_score", "participant"])


def reset_match_participant_info_for_low_bracket_from_hight(
    mathes: QuerySet[Match],
    p_i_m: int,
    advances_to_next: int,
    is_special: list[bool],
    prev_serial_number: int,
    round_cnt: int,
    start_round: int,
) -> None:
    info = []
    prev_math_serial_number = prev_serial_number
    for i, m in enumerate(mathes):
        start_round += 2
        print("start_round", start_round)
        if start_round >= round_cnt - 3:
            print("match id", m.id)
            if is_special[i]:
                print("special")
                match_participant_info_l = ((prev_math_serial_number - 1) * advances_to_next) % (p_i_m)
            else:
                match_participant_info_l = advances_to_next
            print("prev_math_serial_number", prev_math_serial_number)
            print("match_participant_info_l", match_participant_info_l)
            match_participant_info_r = match_participant_info_l + advances_to_next
            for i in m.info.all()[match_participant_info_l:match_participant_info_r]:
                i.participant_score = 0
                i.participant = "---"
                info.append(i)
            prev_math_serial_number = m.serial_number
        else:
            for i in m.info.all():
                i.participant_score = 0
                i.participant = "---"
                info.append(i)
        prev_math_serial_number = m.serial_number

    MatchParticipantInfo.objects.bulk_update(info, ["participant_score", "participant"])


def sort_participant_by_score(match_results: dict, reverse=True):
    return sorted(match_results.keys(), key=lambda x: match_results.get(x).get("score"), reverse=reverse)


def get_last_top_round(round_cnt: int) -> int:
    print("round_cnt", round_cnt)
    round_table = {5: 4, 8: 6, 11: 8, 14: 10, 17: 12, 20: 14, 23: 16}
    return round_table[round_cnt]


def get_next_math_serial_number(serial_number: int, p_i_m: int, advances_to_next: int) -> int:
    flag = 1 if (serial_number % (p_i_m // advances_to_next)) > 0 else 0
    next_serial_number = serial_number // (p_i_m // advances_to_next) + flag
    return next_serial_number


def is_special_low_bracket_round(current_round: int, round_cnt: int) -> bool:
    return (current_round - 3) % 4 == 0 and current_round >= 3 and round_cnt - 1 != current_round


def is_special_top_bracket_round(current_round: int, round_cnt: int) -> bool:
    return (current_round - 2) % 4 == 0 and current_round >= 2


def is_narrowing_round(current_round: int, round_cnt: int) -> bool:
    return (current_round - 5) % 4 == 0 and current_round >= 5


def reflect_number(number, base=4) -> int:
    return base - number + 1


def get_low_bracket_math_serial_number_for_high(
    current_round: int, round_count: int, serial_number: int, p_i_m: int, advances_to_next: int
) -> int:
    if current_round == 0:
        return serial_number // (p_i_m // advances_to_next) + serial_number % (p_i_m // advances_to_next)
    elif current_round == round_count - 3:
        return 1

    return serial_number


def get_low_bracket_math_serial_number(current_round: int, round_count: int, serial_number: int, p_i_m: int) -> int:
    if (current_round - 3) % 4 == 0 and current_round >= 3:
        return math.ceil(serial_number / 2)
    return serial_number


def check_results(prev: list, cur: list) -> bool:
    for i in range(len(prev)):
        if prev[i] != cur[i]:
            return False
    return True


def check_for_draw(match_results: dict) -> bool:
    results = list(match_results.values())
    print("results", results)
    max_scoore = results[0].get("score")
    for result in results:
        if result.get("score") != max_scoore:
            return False
    return True


def set_match_participant_results(match_results: dict, info: MatchParticipantInfo) -> None:
    print("match_results", match_results)
    print("sort_participant_by_score", sort_participant_by_score(match_results))
    if check_for_draw(match_results):
        for result in match_results.values():
            result["participant_result"] = 4
        print("match_results", match_results)
    else:
        winner_match_info_id = sort_participant_by_score(match_results)[0]
        for key in match_results.keys():
            if key == winner_match_info_id:
                match_results.get(key)["participant_result"] = 2
            else:
                match_results.get(key)["participant_result"] = 3
        print("match_results w - l", match_results)

    update_match_participant_info(match_results, info)
