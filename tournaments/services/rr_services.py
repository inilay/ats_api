


from tournaments.services.auxiliary_services import update_match_participant_info

from ..models import (
    Bracket,
    Match,
    MatchParticipantInfo,
    Round,
)


def create_rr_bracket(bracket: Bracket, participants: list):
    participants_cnt = len(participants)
    rounds = []
    unsaved_matches = []
    matches_info = []

    # всегда дополняем до четного
    if participants_cnt % 2 == 1:
        participants = participants + ["---"]
        # смешаем начало на 1
        start = 1
    else:
        start = 0

    permutations = list(range(participants_cnt))
    mid = participants_cnt // 2
    match_serial_number_cnt = 0

    # Создаем раунды
    for number in range(participants_cnt - 1):
        rounds.append(Round(bracket=bracket, serial_number=number))
    Round.objects.bulk_create(rounds)

    # O(n)
    for i, r in enumerate(rounds):
        l1 = permutations[:mid]
        l2 = permutations[mid:]
        # O(n/2)
        l2.reverse()
        # O(n/2)
        for j in range(start, mid):
            match = Match(round=r, serial_number=match_serial_number_cnt, state_id=1)
            unsaved_matches.append(match)
            if j == 0 and i % 2 == 1:
                t2 = participants[l1[j]]
                t1 = participants[l2[j]]
            else:
                t1 = participants[l1[j]]
                t2 = participants[l2[j]]
            matches_info.append(MatchParticipantInfo(match=match, participant_score=0, participant=t1))
            matches_info.append(MatchParticipantInfo(match=match, participant_score=0, participant=t2))
            match_serial_number_cnt = match_serial_number_cnt + 1

        permutations = permutations[mid:-1] + permutations[:mid] + permutations[-1:]

    Match.objects.bulk_create(unsaved_matches)
    MatchParticipantInfo.objects.bulk_create(matches_info)


def update_rr_bracket(data):
    print("data", data)
    match = Match.objects.prefetch_related("info").get(id=data.get("match_id"))
    print("match id", match.id)
    match_prev_state = match.state.name
    cur_match_state = data.get("state")
    match_results = data.get("match_results")

    print("match.state", match.state)
    print(match_prev_state, cur_match_state, match.state.id)

    # S
    if cur_match_state == "SCHEDULED":
        match.state_id = 1
    # P
    else:
        match.state_id = 2
    match.save()
    update_match_participant_info(match_results, match.info.all())
