import math
import secrets
import datetime
from .models import Tournament, Bracket


class MultiStage:
    def __init__(self, participants: list, stage_info: dict, time_managment: dict={}, points: dict={}, second_final: bool=False) -> None:
        self.participants = participants
        self.stage_info = stage_info
        self.time_managment = time_managment
        self.points = points
        self.second_final = second_final
    
    def create_multi_stage_brackets(self) -> dict:  
        brackets = []
        counter = 0
        start = 0
        end = self.stage_info.get('compete_in_group')
        if self.stage_info.get('group_type') == 'SE':
            for i in range(len(self.participants) // self.stage_info.get('compete_in_group')):
                if counter == self.time_managment.get('groups_per_day'): 
                    counter = 0
                    self.time_managment['start_time'] = self.time_managment['start_time'] + datetime.timedelta(seconds=86400)
                group_stage = SingleEl(self.participants[start:end], self.time_managment)
                brackets.append(group_stage.create_se_bracket())
                start += self.stage_info.get('compete_in_group')
                end += self.stage_info.get('compete_in_group')
                counter += 1
            final_time = brackets[-1][-1].get('seeds')[-1].get("startTime")
        elif self.stage_info.get('group_type') == 'DE':
            for i in range(len(self.participants) // self.stage_info.get('compete_in_group')):
                if counter == self.time_managment.get('groups_per_day'): 
                    counter = 0
                    self.time_managment['start_time'] = self.time_managment['start_time'] + datetime.timedelta(seconds=86400)
                group_stage = DoubleEl(self.participants[start:end], self.time_managment)
                brackets.append(group_stage.create_de_bracket())
                start += self.stage_info.get('compete_in_group')
                end += self.stage_info.get('compete_in_group')
                counter += 1  
            final_time = brackets[-1]["upper_rounds"][-1].get('seeds')[-1].get("startTime")
        elif self.stage_info.get('group_type') == 'RR':
            for i in range(len(self.participants) // self.stage_info.get('compete_in_group')):
                if counter == self.time_managment.get('groups_per_day'): 
                    counter = 0
                    self.time_managment['start_time'] = self.time_managment['start_time'] + datetime.timedelta(seconds=86400)
                group_stage = RoundRobin(self.participants[start:end], {'win': 1, 'loss': 0, 'draw': 0}, self.time_managment)
                brackets.append(group_stage.create_round_robin_bracket())
                start += self.stage_info.get('compete_in_group')
                end += self.stage_info.get('compete_in_group')
                counter += 1
            final_time = brackets[-1].get('rounds')[-1][-1].get("startTime")
        else:
            for i in range(len(self.participants) // self.stage_info.get('compete_in_group')):
                if counter == self.time_managment.get('groups_per_day'): 
                    counter = 0
                    self.time_managment['start_time'] = self.time_managment['start_time'] + datetime.timedelta(seconds=86400)
                group_stage = Swiss(self.participants[start:end], {'win': 1, 'loss': 0, 'draw': 0}, self.time_managment)
                brackets.append(group_stage.create_swiss_bracket())
                start += self.stage_info.get('compete_in_group')
                end += self.stage_info.get('compete_in_group')
                counter += 1
            final_time = brackets[-1].get('rounds')[-1][-1].get("startTime")

        TBO_participants = ['TBO' for i in range(len(self.participants) // self.stage_info.get('compete_in_group') * self.stage_info.get('advance_from_group'))] 
        
        if self.time_managment['final_stage_time']:
            self.time_managment['start_time'] = self.time_managment['start_time'] + datetime.timedelta(seconds=86400)
        else:
            final_time = datetime.datetime.strptime(final_time[:16], '%Y-%m-%d %H:%M')
            self.time_managment['start_time'] = self.time_managment['start_time'] - datetime.timedelta(seconds=self.time_managment['start_time'].timestamp()) + datetime.timedelta(seconds=final_time.timestamp()) + datetime.timedelta(minutes=self.time_managment.get('break_between')) + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
        
        if self.stage_info.get('type') == 'SE':
            final_stage = SingleEl(TBO_participants, self.time_managment, self.second_final)
            brackets.append(final_stage.create_se_bracket())
        elif self.stage_info.get('type') == 'DE':
            final_stage = DoubleEl(TBO_participants, self.time_managment)
            brackets.append(final_stage.create_de_bracket())
        elif self.stage_info.get('type') == 'RR':
            final_stage = RoundRobin(TBO_participants, self.points, self.time_managment)
            brackets.append(final_stage.create_round_robin_bracket())
        else:
            final_stage = Swiss(TBO_participants, self.points, self.time_managment)
            brackets.append(final_stage.create_swiss_bracket())

        return brackets

    def set_match_score(match: dict, instance) -> None:
        final_stage = Bracket.objects.get(tournament = instance.tournament, final=True)
        stage_played = True
        if instance.type == 'SE':
            SingleEl.set_match_score(match, instance.bracket)
        elif instance.type == 'RR':
            RoundRobin.set_match_score(match, instance.bracket)
        elif instance.type == 'DE':
            DoubleEl.set_match_score(match, instance.bracket)
        elif instance.type == 'SW':
            Swiss.set_match_score(match, instance.bracket)

        if instance.type == 'RR' or instance.type == 'SW':
            for round in instance.bracket.get('rounds'):
                if stage_played == True:
                    for match in round:
                        # not all match played
                        if match.get("state") == "SCHEDULED":
                            stage_played = False    
                            break

            if stage_played == True:
                if instance.type == 'RR':
                    table = sorted(instance.bracket.get('table'), reverse=True, key=lambda partic: (partic.get('scores'), partic.get('berger')))
                else:
                    table = sorted(instance.bracket.get('table'), reverse=True, key=lambda partic: (partic.get('scores'), partic.get('buchholz')))

        elif instance.type == 'SE':
            for round in instance.bracket:
                if stage_played == True:
                    for match in round.get('seeds'):
                        # not all match played
                        if match.get("state") == "SCHEDULED":
                            stage_played = False
                            break

            if stage_played == True:
                table = []
                for round in instance.bracket[::-1]:
                    for match in round.get('seeds'):
                        if int(match.get('teams')[0].get('score')) > int(match.get('teams')[1].get('score')):
                            if match.get('teams')[0].get('participant') not in table:
                                table.append({'participant': match.get('teams')[0].get('participant')})
                            if match.get('teams')[1].get('participant') not in table:
                                table.append({'participant': match.get('teams')[1].get('participant')})
                        else:
                            if match.get('teams')[1].get('participant') not in table:
                                table.append({'participant': match.get('teams')[1].get('participant')})
                            if match.get('teams')[0].get('participant') not in table:
                                table.append({'participant': match.get('teams')[0].get('participant')})

        elif instance.type == 'DE':
            for round in instance.bracket["upper_rounds"]:
                if stage_played == True:
                    for match in round.get('seeds'):
                        # not all match played
                        if match.get("state") == "SCHEDULED":
                            stage_played = False
                            break

            if stage_played == True:
                table = []
                for round in instance.bracket['upper_rounds'][::-1]:
                    for match in round.get('seeds'):
                        if int(match.get('teams')[0].get('score')) > int(match.get('teams')[1].get('score')):
                            if {'participant': match.get('teams')[0].get('participant')} not in table:
                                table.append({'participant': match.get('teams')[0].get('participant')})
                            if {'participant': match.get('teams')[1].get('participant')} not in table:
                                table.append({'participant': match.get('teams')[1].get('participant')})
                        else:
                            if {'participant': match.get('teams')[1].get('participant')} not in table:
                                table.append({'participant': match.get('teams')[1].get('participant')})
                            if {'participant': match.get('teams')[0].get('participant')} not in table:
                                table.append({'participant': match.get('teams')[0].get('participant')})

        if stage_played == True:
            if final_stage.type == 'SE':    
                SingleEl.fill_participants(instance, table)
            elif final_stage.type == 'DE':
                DoubleEl.fill_participants(instance, table)
            elif final_stage.type == 'SW':
                Swiss.fill_participants(instance, table)
            elif final_stage.type == 'RR':
                RoundRobin.fill_participants(instance, table)


class RoundRobin:

    def __init__(self, participants: list, points: dict, time_managment: dict={}) -> None:
        self.participants = [self.append_participant(name) for name in participants]
        self.match_table = [self.append_participant_to_table(name) for name in participants]
        self.points = points
        self.time_managment = time_managment

    @staticmethod
    def fill_participants(instance: Bracket, participants: dict):
        final = Bracket.objects.get(tournament = instance.tournament, final=True)
        # print(instance.bracket[0]['seeds'][0]['teams'][0]['participant'])
        part_for_check = participants[:]
        for j in participants[:final.participants_from_group]:
            for round in final.bracket['rounds']:
                fill_part = False
                for match in round:
                    if match.get('participants')[0].get('participant') == 'TBO':
                        fill_id = match.get('participants')[0].get('id')
                        fill_part = True
                        for round in final.bracket['rounds']:
                            for match in round:
                                if match.get('participants')[0].get('id') == fill_id:
                                    match['participants'][0]['participant'] = j.get('participant')
                                elif match.get('participants')[1].get('id') == fill_id:
                                    match['participants'][1]['participant'] = j.get('participant')
                        break
                    
                    elif match.get('participants')[1].get('participant') == 'TBO':
                        fill_id = match.get('participants')[1].get('id')
                        fill_part = True
                        for round in final.bracket['rounds']:
                            for match in round:
                                if match.get('participants')[0].get('id') == fill_id:
                                    match['participants'][0]['participant'] = j.get('participant')
                                elif match.get('participants')[1].get('id') == fill_id:
                                    match['participants'][1]['participant'] = j.get('participant')
                        break

                if fill_part == True:
                    fill_part = False
                    break
                
            for row in final.bracket['table']:
                if row.get('participant') == "TBO":
                    row['participant'] = j.get('participant')
                    break
                

        final.save()

    @staticmethod
    def set_match_score(match: dict, bracket) -> None:
        round_id = match.get('round_id')
        match_id = match.get('match_id')
        prev_match_state = bracket.get('rounds')[round_id][match_id]

        current_first_res = int(match.get('participants')[0].get('score'))
        current_second_res = int(match.get('participants')[1].get('score'))
        
        first_partic_res = current_first_res - int(prev_match_state.get('participants')[0].get('score'))
        second_partic_res = current_second_res - int(prev_match_state.get('participants')[1].get('score'))
        
        # generators search participant in table O(n)
        first_partic = next(partic for partic in bracket.get('table') if partic['participant'] == match.get('participants')[0].get('participant'))
        second_partic = next(partic for partic in bracket.get('table') if partic['participant'] == match.get('participants')[1].get('participant'))
        # add match scoore to table 
        first_partic.get('match_w_l')[0] += first_partic_res
        first_partic.get('match_w_l')[1] += second_partic_res
        second_partic.get('match_w_l')[0] += second_partic_res
        second_partic.get('match_w_l')[1] += first_partic_res
       
        # S -> P
        if match.get('state') == "PLAYED" and prev_match_state.get('state') == 'SCHEDULED':
            match['state'] = "PLAYED"
            if current_first_res > current_second_res:
                # add res in table
                first_partic['win'] += 1
                second_partic['loose'] += 1
            elif current_second_res > current_first_res:
                # add res in table
                second_partic['win'] += 1
                first_partic['loose'] += 1
            elif current_second_res == 0 and match.get('participants')[0].get('score') == 0:
                if current_first_res - current_second_res < 0:
                    second_partic['win'] += 1
                    first_partic['loose'] += 1
                elif current_first_res - current_second_res > 0:
                    first_partic['win'] += 1
                    second_partic['loose'] += 1
                else:
                    second_partic['draw'] += 1
                    first_partic['draw'] += 1
            else:
                second_partic['draw'] += 1
                first_partic['draw'] += 1
        # P -> S
        elif match.get('state') == "SCHEDULED" and prev_match_state.get('state') == 'PLAYED':
            match['state'] = "SCHEDULED"
            if  prev_match_state.get('participants')[0]['isWinner'] == True:
                # add res in table
                first_partic['win'] -= 1
                second_partic['loose'] -= 1
            elif prev_match_state.get('participants')[1]['isWinner'] == True:
                # add res in table
                second_partic['win'] -= 1
                first_partic['loose'] -= 1
            else:
                second_partic['draw'] -= 1
                first_partic['draw'] -= 1
        # P -> P
        elif match.get('state') == "PLAYED" and prev_match_state.get('state') == 'PLAYED':
            # d -> 1
            if prev_match_state.get('participants')[0]['isWinner'] == False and \
                prev_match_state.get('participants')[1]['isWinner'] == False and match.get('participants')[0]['isWinner']==True:
                first_partic['win'] += 1
                first_partic['draw'] -= 1
                second_partic['draw'] -= 1
                second_partic['loose'] += 1
            # d -> 2
            elif prev_match_state.get('participants')[0]['isWinner'] == False and \
                prev_match_state.get('participants')[1]['isWinner'] == False and match.get('participants')[1]['isWinner']==True:
                second_partic['win'] += 1
                second_partic['draw'] -= 1
                first_partic['draw'] -= 1
                first_partic['loose'] += 1
            # 2 -> 1
            elif match.get('participants')[0]['isWinner'] == True and prev_match_state.get('participants')[0]['isWinner']==False:
                first_partic['win'] += 1
                first_partic['loose'] -= 1
                second_partic['loose'] += 1
                second_partic['win'] -= 1
            # 1 -> 2
            elif match.get('participants')[1]['isWinner'] == True and prev_match_state.get('participants')[1]['isWinner']==False:
                second_partic['win'] += 1
                second_partic['loose'] -= 1
                first_partic['loose'] += 1
                first_partic['win'] -= 1
            # 1 -> d
            elif match.get('participants')[0]['isWinner'] == False and \
                match.get('participants')[1]['isWinner'] == False and prev_match_state.get('participants')[0]['isWinner']==True:
                first_partic['win'] -= 1
                first_partic['draw'] += 1
                second_partic['draw'] += 1
                second_partic['loose'] -= 1
            # 2 -> d
            elif match.get('participants')[0]['isWinner'] == False and \
                match.get('participants')[1]['isWinner'] == False and prev_match_state.get('participants')[1]['isWinner']==True:
                second_partic['win'] -= 1
                second_partic['draw'] += 1
                first_partic['draw'] += 1
                first_partic['loose'] -= 1

        # get score from table
        win_scoore = bracket.get('points').get('win')
        loos_scoore = bracket.get('points').get('loss')
        draw_scoore = bracket.get('points').get('draw')

        # calc for participants
        first_partic['scores'] = first_partic['draw']*draw_scoore + first_partic['win']*win_scoore + first_partic['loose']*loos_scoore
        second_partic['scores'] = second_partic['draw']*draw_scoore + second_partic['win']*win_scoore + second_partic['loose']*loos_scoore

        # delete round and match id
        match.pop('round_id')
        match.pop('match_id')
        bracket.get('rounds')[round_id][match_id] = match

        # Berger
        # O(n/2 * log(n))
        for count, i in enumerate(bracket.get('rounds')[0:round_id+1]):
            for j in i:
                # O(n)
                first = next(partic for partic in bracket.get('table') if partic['participant'] == j.get('participants')[0].get('participant'))
                second = next(partic for partic in bracket.get('table') if partic['participant'] == j.get('participants')[1].get('participant'))
                if count == 0:
                    first['berger'] = 0
                    second['berger'] = 0
                if j.get('participants')[0]['isWinner'] == True:
                    first['berger'] += second['scores']
                elif j.get('participants')[1]['isWinner'] == True:
                    second['berger'] += first['scores']
                elif match.get('state') == "PLAYED" and j.get('participants')[0]['isWinner'] == False and j.get('participants')[1]['isWinner'] == False:
                    first['berger'] += 1/2 * second['scores']
                    second['berger'] += 1/2 * first['scores']
    

    def append_participant(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'score': 0,
                    'participant': f"{name}",
                    'isWinner': False
                }
    
    def append_participant_to_table(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'participant': f"{name}",
                    'match_w_l': [0, 0],
                    'draw': 0,
                    'win': 0,
                    'loose': 0,
                    'scores': 0,
                    'berger': 0
                }

    def create_round_robin_bracket(self) -> dict:  
        round_robin_bracket = []
        # всегда дополняем до четного
        if len(self.participants) % 2 == 1: 
            self.participants = self.participants + [self.append_participant('None')] 
            # смешаем начало на 1
            start = 1 
            # if len(self.participants) // 2 != 1 else 0
        else:   
            start = 0

        n = len(self.participants)
        # permutations ?
        permutations = list(range(n))
        mid = n // 2 
       
        # O(n)
        for i in range(n-1):
            l1 = permutations[:mid]
            l2 = permutations[mid:]
            l2.reverse()
            round = []
            # O(n/2)
            for j in range(start, mid):
                t1 = self.participants[l1[j]]
                t2 = self.participants[l2[j]]
                if j == 0 and i % 2 == 1:
                    print('work')
                    round.append({
                    "id": secrets.token_hex(16),
                    "startTime": f"{self.time_managment.get('start_time')}",
                    "state": "SCHEDULED",
                    "participants": [
                        t2,
                        t1
                    ]
                    })
                else:
                    round.append({
                    "id": secrets.token_hex(16),
                    "startTime": f"{self.time_managment.get('start_time')}",
                    "state": "SCHEDULED",
                    "participants": [
                        t1,
                        t2
                    ]
                    })
            round_robin_bracket.append(round)
            permutations = permutations[mid:-1] + permutations[:mid] + permutations[-1:]

        # Time managment
        if self.time_managment.get('time_managment'):
            last_time = self.time_managment.get('start_time')
            for counter, round in enumerate(round_robin_bracket):
                if counter == 0:
                    for i in range(self.time_managment.get('mathes_same_time'), len(round), self.time_managment.get('mathes_same_time')):
                        for game in round[i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                else:
                     for i in range(0, len(round), self.time_managment.get('mathes_same_time')):
                        for game in round[i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('break_between'))
     
        return {'rounds': round_robin_bracket, 'table': self.match_table, 'points': self.points}
    

class SingleEl:

    def __init__(self, participants: dict, time_managment: dict={}, second_final: bool=False) -> None:
        self.participants = [self.append_participant(name) for name in participants]
        self.second_final = second_final
        self.length = len(participants)
        self.time_managment = time_managment

    def single_el_number_of_rounds(self) -> int:
        return math.ceil(math.log2(len(self.participants)))

    def append_participant(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'participant': f"{name}",
                    'score': 0,
                    'isWinner': False
                }

    def get_participant(self) -> dict:
        if self.participants:
            return self.participants.pop()
        return self.append_participant('---')

    def get_match(self, full: bool=True) -> dict:
        if full:
            second_participant = self.get_participant()
        else:
            second_participant = self.append_participant('---')
        return  {
                'id': secrets.token_hex(16),
                "startTime": f"{self.time_managment.get('start_time')}",
                "state": "SCHEDULED",
                'teams': [
                    self.get_participant(),
                    second_participant
                ]
            }
    @staticmethod
    def fill_participants(instance: Bracket, participants: dict):
        final = Bracket.objects.get(tournament = instance.tournament, final=True)
        print(instance)
        for j in participants[:final.participants_from_group]:
            for i in range(len(final.bracket[0]['seeds']) // 2):
                
                if final.bracket[0]['seeds'][i].get('teams')[0].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][i]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket[0]['seeds'][len(final.bracket[0]['seeds']) // 2 + i].get('teams')[0].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][len(final.bracket[0]['seeds']) // 2 + i]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket[0]['seeds'][i].get('teams')[1].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][i]['teams'][1]['participant'] = j.get('participant')
                    break

                elif final.bracket[0]['seeds'][len(final.bracket[0]['seeds']) // 2 + i].get('teams')[1].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][len(final.bracket[0]['seeds']) // 2 + i]['teams'][1]['participant'] = j.get('participant')
                    break
            if (len(final.bracket[0]['seeds']) // 2 == 0):
                if final.bracket[0]['seeds'][0].get('teams')[0].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][0]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket[0]['seeds'][0].get('teams')[1].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][0]['teams'][1]['participant'] = j.get('participant')
                    break

   
        final.save()
                

    @staticmethod
    def set_match_score(current_match, bracket) -> None:
        round_id = current_match.get('round_id')
        match_id = current_match.get('match_id')
        prev_match = bracket[round_id]['seeds'][match_id]
        
        current_match.pop('round_id')
        current_match.pop('match_id')
        bracket[round_id]['seeds'][match_id] = current_match

        # P -> S
        if prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "SCHEDULED":
            cur_i = match_id
            # from the current round to the end
            for i in range(round_id, len(bracket)-1):
                if cur_i % 2 == 0:
                    cur_i = cur_i - (cur_i // 2) 
                    team_index = 0
                else:
                    cur_i = cur_i - (cur_i // 2) - 1
                    team_index = 1
                # 3 round and double final
                if bracket[i] == bracket[-2] and len(bracket[-1]['seeds']) == len(bracket[-2]['seeds']):
                    # split the grid horizontally if at the bottom 1 otherwise 0
                    team_index = 1 if match_id >= len(bracket[round_id]['seeds']) // 2 else 0
                bracket[i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                bracket[i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                bracket[i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                bracket[i+1]['seeds'][cur_i]['teams'][team_index-1]['score']  = 0
                bracket[i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
        # P -> P
        elif prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "PLAYED":
            current_winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
            prev_winner = 1 if int(prev_match['teams'][0]['score']) < int(prev_match['teams'][1]['score'])  else 0
            if current_winner != prev_winner:
                # rollback
                cur_i = match_id
                # from the current round to the end
                # O(log(n))
                for i in range(round_id, len(bracket)-1):
                    if cur_i % 2 == 0:
                        cur_i = cur_i - (cur_i // 2) 
                        team_index = 0
                    else:
                        cur_i = cur_i - (cur_i // 2) - 1
                        team_index = 1
                    # 3 round and double final
                    if bracket[i] == bracket[-2] and len(bracket[-1]['seeds']) == len(bracket[-2]['seeds']):
                        # split the grid horizontally if at the bottom 1 otherwise 0
                        team_index = 1 if match_id >= len(bracket[round_id]['seeds']) // 2 else 0
                    bracket[i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                    bracket[i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                    bracket[i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                    bracket[i+1]['seeds'][cur_i]['teams'][team_index-1]['score']  = 0
                    bracket[i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                # forward
                if bracket[round_id] != bracket[-1] and len(bracket[round_id]['seeds']) != len(bracket[-1]['seeds']):
                    if match_id % 2 == 0:
                        match_index =  match_id - (match_id // 2)
                        team_index = 0
                    else:
                        match_index = match_id - (match_id // 2) - 1
                        team_index = 1

                    bracket[round_id+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][current_winner]['participant']
                    bracket[round_id+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][current_winner]['id']

                    # check for second final
                    if bracket[round_id] != bracket[-2] and len(bracket[round_id+1]['seeds']) == len(bracket[round_id+2]['seeds']):
                        bracket[round_id+2]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][current_winner-1]['participant']
                        bracket[round_id+2]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][current_winner-1]['id']
        # S -> P
        elif prev_match.get('state')  == "SCHEDULED" and current_match.get('state')  == "PLAYED": 
            winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
            if bracket[round_id] != bracket[-1] and len(bracket[round_id]['seeds']) != len(bracket[-1]['seeds']):

                if match_id % 2 == 0:
                    match_index =  match_id - (match_id // 2)
                    team_index = 0
                else:
                    match_index = match_id - (match_id // 2) - 1
                    team_index = 1
                    
                bracket[round_id+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][winner]['participant']
                bracket[round_id+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][winner]['id']

                # check for second final
                if bracket[round_id] != bracket[-2] and len(bracket[round_id+1]['seeds']) == len(bracket[round_id+2]['seeds']):
                    bracket[round_id+2]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][winner-1]['participant']
                    bracket[round_id+2]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][winner-1]['id']

    def create_se_bracket(self) -> list:
        rounds = []
        nummber_of_rounds = self.single_el_number_of_rounds()
        number_of_match = 2**(nummber_of_rounds-1)
        # if not power of two
        # if number_of_match != self.length:
        # number_of_match = number_of_match // 2
        
        full_first = self.length - number_of_match

        # create firs round
        first_round = {'title': 0, 'seeds': []}
        # O(n)
        for j in range(int(number_of_match)):
            if full_first > 0:
                first_round.get('seeds').append(self.get_match())
                full_first -= 1
            else:
                first_round.get('seeds').append(self.get_match(full=False))
        rounds.append(first_round)

        # create second round
        # second_round = {'title': 1, 'seeds': []}
        # # O(n)
        # # for j in range(int(number_of_match / 2 )):
        # #     second_round.get('seeds').append(self.get_match())
                
        # rounds.append(second_round)
        
        if nummber_of_rounds > 1:
            # O(log(n))
            for i in range(1, nummber_of_rounds):
                round = {'title': i+1, 'seeds': []}
                # O(n)
                for j in range(int(number_of_match / 2**i )):
                    round.get('seeds').append(self.get_match())
                rounds.append(round)
        # else:
        #     # O(log(n))
        #     for i in range(1, nummber_of_rounds+1):
        #         round = {'title': i, 'seeds': []}
        #         # O(n)
        #         for j in range(int(number_of_match / 2**i )):
        #             round.get('seeds').append(self.get_match())
        #         rounds.append(round)
        # add second final
        if self.second_final:
            rounds.append({'title': 'Final for 3 place', 'seeds': [self.get_match()]})

        # Time managment
        if self.time_managment.get('time_managment'):
            last_time = self.time_managment.get('start_time')
            # O(log(n))
            for counter, round in enumerate(rounds):
                if counter == 0:
                    for i in range(self.time_managment.get('mathes_same_time'), len(round["seeds"]), self.time_managment.get('mathes_same_time')):
                        for game in round["seeds"][i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                else:
                     for i in range(0, len(round["seeds"]), self.time_managment.get('mathes_same_time')):
                        for game in round["seeds"][i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('break_between'))
        # else:
        #      for counter, round in enumerate(rounds):
        #         for game in round["seeds"]:
        #             game['startTime'] = f"{self.time_managment.get('start_time')}"
        
        return rounds


class DoubleEl:

    def __init__(self, participants: list, time_managment: dict={}) -> None:
        self.participants = [self.append_participant(name) for name in participants]
        self.length = len(participants)
        self.time_managment = time_managment

    def single_el_number_of_rounds(self) -> int:
        return math.ceil(math.log2(len(self.participants)))

    def append_participant(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'participant': f"{name}",
                    'score': 0,
                    'isWinner': False
                }

    def get_participant(self) -> dict:
        if self.participants:
            return self.participants.pop()
        return self.append_participant('---')

    def get_match(self, full: bool=True) -> dict:
        if full:
            second_participant = self.get_participant()
        else:
            second_participant = self.append_participant('---')
        return  {
                'id': secrets.token_hex(16),
                "startTime": f"{self.time_managment.get('start_time')}",
                # "startTime": f"2023-06-8",
                "state": "SCHEDULED",
                'teams': [
                    self.get_participant(),
                    second_participant
                ]
            }
    
    @staticmethod
    def fill_participants(instance: Bracket, participants: dict):
        final = Bracket.objects.get(tournament = instance.tournament, final=True)
        # print(instance.bracket[0]['seeds'][0]['teams'][0]['participant'])
        for j in participants[:final.participants_from_group]:
            for i in range(len(final.bracket['upper_rounds'][0]['seeds']) // 2):
                if final.bracket['upper_rounds'][0]['seeds'][i].get('teams')[0].get('participant') == 'TBO':
                    final.bracket['upper_rounds'][0]['seeds'][i]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket['upper_rounds'][0]['seeds'][len(final.bracket['upper_rounds'][0]['seeds']) // 2 + i].get('teams')[0].get('participant') == 'TBO':
                    final.bracket['upper_rounds'][0]['seeds'][len(final.bracket['upper_rounds'][0]['seeds']) // 2 + i]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket['upper_rounds'][0]['seeds'][i].get('teams')[1].get('participant') == 'TBO':
                    final.bracket['upper_rounds'][0]['seeds'][i]['teams'][1]['participant'] = j.get('participant')
                    break

                elif final.bracket['upper_rounds'][0]['seeds'][len(final.bracket['upper_rounds'][0]['seeds']) // 2 + i].get('teams')[1].get('participant') == 'TBO':
                    final.bracket['upper_rounds'][0]['seeds'][len(final.bracket['upper_rounds'][0]['seeds']) // 2 + i]['teams'][1]['participant'] = j.get('participant')
                    break

            if (len(final.bracket[0]['seeds']) // 2 == 0):
                if final.bracket[0]['seeds'][0].get('teams')[0].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][0]['teams'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket[0]['seeds'][0].get('teams')[1].get('participant') == 'TBO':
                    final.bracket[0]['seeds'][0]['teams'][1]['participant'] = j.get('participant')
                    break

        final.save()

    @staticmethod
    def set_match_score(current_match, bracket) -> None:
        # upper
        for r_index, round in enumerate(bracket['upper_rounds']):
            # search match
            for m_index, prev_match in enumerate(round['seeds']):
                if prev_match.get('id') == current_match.get('id'):
                    round['seeds'][m_index] = current_match
                    # P -> S
                    if prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "SCHEDULED":
                        cur_i = m_index
                        # from the current round to the end
                        # O(log(n))
                        for i in range(r_index, len(bracket['upper_rounds'])-1):
                            if cur_i % 2 == 0:
                                cur_i = cur_i - (cur_i // 2) 
                                team_index = 0
                            else:
                                cur_i = cur_i - (cur_i // 2) - 1
                                team_index = 1
                            bracket['upper_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                            bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                            bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                            bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                        # indexs for lower bracket
                        if r_index == 0:
                            if m_index % 2 == 0:
                                match_index_lower = m_index - (m_index // 2)
                                team_index_lower = 0
                            else:
                                match_index_lower = m_index - (m_index // 2) - 1 
                                team_index_lower = 1
                        # not first round
                        else:
                            match_index_lower = len(round['seeds']) - 1 - m_index if m_index != 0 else -1
                            team_index_lower = 1
                        if r_index > 1:
                            round_index_lower = r_index + r_index - 1
                        else:
                            round_index_lower = r_index
                        bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['state'] = "SCHEDULED"
                        bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['score'] = 0
                        bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['participant'] = "---"
                        bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['id'] = secrets.token_hex(16)
                        # from the current lower bracket round to the end
                        for i in range(round_index_lower, len(bracket['lower_rounds'])-1):
                            if cur_i % 2 == 0:
                                cur_i = cur_i - (cur_i // 2) if i % 2 == 1 else cur_i
                                team_index = 0
                            else:
                                cur_i = cur_i - (cur_i // 2) - 1 if i % 2 == 1 else cur_i
                                team_index = 1 if i % 2 else 0
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                        
                        # check last
                        lower_winner = 0 if int(prev_match['teams'][0]['score']) < int(prev_match['teams'][1]['score'])  else 1

                        if bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] == current_match['teams'][lower_winner]['id']:
                            bracket['upper_rounds'][-1]['seeds'][-1]['state'] = "SCHEDULED"
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = "---"
                            bracket['upper_rounds'][1]['seeds'][-1]['teams'][1]['score']  = 0
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = secrets.token_hex(16)

                    # P -> P
                    elif prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "PLAYED":
                        current_winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
                        prev_winner = 1 if int(prev_match['teams'][0]['score']) < int(prev_match['teams'][1]['score'])  else 0
                        if current_winner != prev_winner:
                        # rollback
                            cur_i = m_index
                            for i in range(r_index, len(bracket['upper_rounds'])-1):
                                if cur_i % 2 == 0:
                                    cur_i = cur_i - (cur_i // 2) 
                                    team_index = 0
                                else:
                                    cur_i = cur_i - (cur_i // 2) - 1
                                    team_index = 1
                                bracket['upper_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                                bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                                bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                                bracket['upper_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                            # indexs for lower bracket
                            if r_index == 0:
                                if m_index % 2 == 0:
                                    match_index_lower = m_index - (m_index // 2)
                                    team_index_lower = 0
                                else:
                                    match_index_lower = m_index - (m_index // 2) - 1 
                                    team_index_lower = 1
                            # not first round
                            else:
                                match_index_lower = len(round['seeds']) - 1 - m_index if m_index != 0 else -1
                                team_index_lower = 1

                            if r_index > 1:
                                round_index_lower = r_index + r_index - 1
                            else:
                                round_index_lower = r_index
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['state'] = "SCHEDULED"
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['score'] = 0
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['participant'] = "---"
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['id'] = secrets.token_hex(16)
                            # check last
                            lower_winner = 0 if int(prev_match['teams'][0]['score']) < int(prev_match['teams'][1]['score'])  else 1

                            if bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] == current_match['teams'][lower_winner]['id']:

                                bracket['upper_rounds'][-1]['seeds'][-1]['state'] = "SCHEDULED"
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = "---"
                                bracket['upper_rounds'][1]['seeds'][-1]['teams'][1]['score']  = 0
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = secrets.token_hex(16)
                            # from the current lower bracket round to the end
                            for i in range(round_index_lower, len(bracket['lower_rounds'])-1):
                                if cur_i % 2 == 0:
                                    cur_i = cur_i - (cur_i // 2) if i % 2 == 1 else cur_i
                                    team_index = 0
                                else:
                                    cur_i = cur_i - (cur_i // 2) - 1 if i % 2 == 1 else cur_i
                                    team_index = 1 if i % 2 else 0
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                            # forward
                            if bracket['upper_rounds'][r_index] != bracket['upper_rounds'][-1] and len(bracket['upper_rounds'][r_index]['seeds']) != len(bracket['upper_rounds'][-1]['seeds']):
                                if m_index % 2 == 0:
                                    match_index =  m_index - (m_index // 2)
                                    team_index = 0
                                else:
                                    match_index = m_index - (m_index // 2) - 1
                                    team_index = 1

                                bracket['upper_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][current_winner]['participant']
                                bracket['upper_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][current_winner]['id']
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['participant'] = current_match['teams'][current_winner-1]['participant']
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['id'] = current_match['teams'][current_winner-1]['id']
                    
                    # S -> P
                    elif prev_match.get('state')  == "SCHEDULED" and current_match.get('state')  == "PLAYED": 
                        winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
                        # not last
                        if bracket['upper_rounds'][r_index] != bracket['upper_rounds'][-1]:
                            if m_index % 2 == 0:
                                match_index =  m_index - (m_index // 2)
                                team_index = 0
                            else:
                                match_index = m_index - (m_index // 2) - 1
                                team_index = 1

                            bracket['upper_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][winner]['participant']
                            bracket['upper_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][winner]['id']
                            # indexs for lower bracket
                            if r_index == 0:
                                if m_index % 2 == 0:
                                    match_index_lower = m_index - (m_index // 2)
                                    team_index_lower = 0
                                else:
                                    match_index_lower = m_index - (m_index // 2) - 1 
                                    # len(round['seeds']) - 1 - m_index
                                    team_index_lower = 1
                            # not first round
                            else:
                                match_index_lower = len(round['seeds']) - 1 - m_index if m_index != 0 else -1
                                team_index_lower = 1

                            if r_index > 1:
                                round_index_lower = r_index + r_index - 1
                            else:
                                round_index_lower = r_index

                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['participant'] = current_match['teams'][winner-1]['participant']
                            bracket['lower_rounds'][round_index_lower]['seeds'][match_index_lower]['teams'][team_index_lower]['id'] = current_match['teams'][winner-1]['id']
                    # leave function
                    return
        #lower
        for r_index, round in enumerate(bracket['lower_rounds']):
            # search match
            for m_index, prev_match in enumerate(round['seeds']):
                if prev_match.get('id') == current_match.get('id'):
                    # set score for cur match
                    round['seeds'][m_index] = current_match
                    # P -> S
                    if prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "SCHEDULED":
                        cur_i = m_index
                        # rollback
                        # from the current round to the end
                        for i in range(r_index, len(bracket['lower_rounds'])-1):
                            if cur_i % 2 == 0:
                                cur_i = cur_i - (cur_i // 2) if i % 2 == 1 else cur_i
                                team_index = 0
                            else:
                                cur_i = cur_i - (cur_i // 2) - 1 if i % 2 == 1 else cur_i
                                team_index = 1 if i % 2 else 0
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index-1]['score']  = 0
                            bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)
                        
                        # # check last
                        # lower_winner = 1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
                        # if bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] == current_match['teams'][lower_winner]['id']:
                            bracket['upper_rounds'][-1]['seeds'][-1]['state'] = "SCHEDULED"
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = "---"
                            bracket['upper_rounds'][1]['seeds'][-1]['teams'][1]['score']  = 0
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = secrets.token_hex(16)
                    # P -> P
                    elif prev_match.get('state')  == "PLAYED" and current_match.get('state')  == "PLAYED":
                        current_winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
                        prev_winner = 1 if int(prev_match['teams'][0]['score']) < int(prev_match['teams'][1]['score'])  else 0
                        if current_winner != prev_winner:
                            # rollback
                            cur_i = m_index
                            for i in range(r_index, len(bracket['lower_rounds'])-1):
                                if cur_i % 2 == 0:
                                    cur_i = cur_i - (cur_i // 2) if r_index % 2 else cur_i
                                    team_index = 0
                                else:
                                    cur_i = cur_i - (cur_i // 2) - 1 if r_index % 2 else cur_i
                                    team_index = 1 if i % 2 else 0
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['state'] = "SCHEDULED"
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['participant']  = "---"
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['score']  = 0
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index-1]['score']  = 0
                                bracket['lower_rounds'][i+1]['seeds'][cur_i]['teams'][team_index]['id'] = secrets.token_hex(16)

                                bracket['upper_rounds'][-1]['seeds'][-1]['state'] = "SCHEDULED"
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = "---"
                                bracket['upper_rounds'][1]['seeds'][-1]['teams'][1]['score']  = 0
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = secrets.token_hex(16)
                            # forward
                            if bracket['lower_rounds'][r_index] != bracket['lower_rounds'][-1]:
                                if m_index % 2 == 0:
                                    match_index =  m_index - (m_index // 2) if r_index % 2 else m_index
                                    team_index = 0
                                else:
                                    match_index = m_index - (m_index // 2) - 1 if r_index % 2 else m_index
                                    team_index = 1 if r_index % 2 else 0

                                bracket['lower_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][current_winner]['participant']
                                bracket['lower_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][current_winner]['id']
                            else:
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = current_match['teams'][current_winner]['participant']
                                bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = current_match['teams'][current_winner]['id']
                    # S -> P
                    elif prev_match.get('state')  == "SCHEDULED" and current_match.get('state')  == "PLAYED": 
                       
                        winner =  1 if int(current_match['teams'][0]['score']) < int(current_match['teams'][1]['score'])  else 0
                        # not last 
                        if bracket['lower_rounds'][r_index] != bracket['lower_rounds'][-1]:
                            if m_index % 2 == 0:
                                match_index =  m_index - (m_index // 2) if r_index % 2 else m_index
                                team_index = 0 
                            else:
                                match_index = m_index - (m_index // 2) - 1 if r_index % 2 else m_index
                                team_index = 1 if r_index % 2 else 0

                            bracket['lower_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['participant'] = current_match['teams'][winner]['participant']
                            bracket['lower_rounds'][r_index+1]['seeds'][match_index]['teams'][team_index]['id'] = current_match['teams'][winner]['id']
                        else:
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['participant'] = current_match['teams'][winner]['participant']
                            bracket['upper_rounds'][-1]['seeds'][-1]['teams'][1]['id'] = current_match['teams'][winner]['id']
                    # leave function
                    return

    def create_de_bracket(self) -> list:
        upper_rounds = []
        lower_rounds = []
        nummber_of_rounds = self.single_el_number_of_rounds()
        number_of_match = 2**(nummber_of_rounds - 1)

        # if not power of two
        # if number_of_match != self.length:
        #     number_of_match = number_of_match // 2
        full_first = self.length - number_of_match

        # create firs round
        first_round = {'title': 0, 'seeds': []}
        # O(n)
        for j in range(int(number_of_match)):
            if full_first > 0:
                first_round.get('seeds').append(self.get_match())
                full_first -= 1
            else:
                first_round.get('seeds').append(self.get_match(full=False))
        upper_rounds.append(first_round)
        
        # create second round
        # second_round = {'title': 1, 'seeds': []}
        # # O(n)
        # for j in range(int(number_of_match / 2 )):
        #     second_round.get('seeds').append(self.get_match())
                
        # upper_rounds.append(second_round)
        
        if nummber_of_rounds > 1:
            # O(log(n))
            for i in range(1, nummber_of_rounds):
                round = {'title': i+1, 'seeds': []}
                # O(n)
                for j in range(int(number_of_match / 2**i )):
                    round.get('seeds').append(self.get_match())
                upper_rounds.append(round)
        # else:
        #     # O(log(n))
        #     for i in range(1, nummber_of_rounds+1):
        #         round = {'title': i, 'seeds': []}
        #         # O(n)
        #         for j in range(int(number_of_match / 2**i )):
        #             round.get('seeds').append(self.get_match())
        #         upper_rounds.append(round)

        upper_rounds.append({'title': 'Final for 3 place', 'seeds': [self.get_match()]})
       
        #create lower
        # O(log(n))
        for i in range(2, nummber_of_rounds+1):
            round_1 = {'title': i, 'seeds': []}
            round_2 = {'title': i, 'seeds': []}
            # O(n)
            for j in range(int(2**nummber_of_rounds / 2**i)):
                round_1.get('seeds').append(self.get_match())
                round_2.get('seeds').append(self.get_match())
            lower_rounds.append(round_1)
            lower_rounds.append(round_2)

        # Time managment
        if self.time_managment.get('time_managment'):
            last_time = self.time_managment.get('start_time')
            # upper bracket
            # O(log(n))
            for counter, round in enumerate(upper_rounds[:-1]):
                if counter == 0:
                    for i in range(self.time_managment.get('mathes_same_time'), len(round["seeds"]), self.time_managment.get('mathes_same_time')):
                        for game in round["seeds"][i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                else:
                     for i in range(0, len(round["seeds"]), self.time_managment.get('mathes_same_time')):
                        for game in round["seeds"][i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('break_between'))
            # lower bracket
            # O(log(n))
            for round in lower_rounds:
                for i in range(0, len(round["seeds"]), self.time_managment.get('mathes_same_time')):
                    for game in round["seeds"][i:i+self.time_managment.get('mathes_same_time')]:
                        game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                    last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('break_between'))
            upper_rounds[-1]["seeds"][0]['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
        
        return {'upper_rounds': upper_rounds, 'lower_rounds': lower_rounds}


class Swiss:
    def __init__(self, participants: list, points: dict, time_managment: dict={}) -> None:
        print(participants)
        self.participants = [self.append_participant(name) for name in participants]
        self.match_table = [self.append_participant_to_table(name) for name in participants]
        self.points = points
        self.time_managment = time_managment

    @staticmethod
    def fill_participants(instance: Bracket, participants: dict):
        final = Bracket.objects.get(tournament = instance.tournament, final=True)
        # print(instance.bracket[0]['seeds'][0]['teams'][0]['participant'])
  
        for j in participants[:final.participants_from_group]:
            for i in range(len(final.bracket['rounds'][0]) // 2):
                if final.bracket['rounds'][0][i].get('participants')[0].get('participant') == 'TBO':
                    final.bracket['rounds'][0][i]['participants'][0]['participant'] = j.get('participant')
                    print(1)
                    break
                
                elif final.bracket['rounds'][0][len(final.bracket['rounds'][0]) // 2 + i].get('participants')[0].get('participant') == 'TBO':
                    final.bracket['rounds'][0][len(final.bracket['rounds'][0]) // 2 + i]['participants'][0]['participant'] = j.get('participant')
                    print(3)
                    break


                elif final.bracket['rounds'][0][i].get('participants')[1].get('participant') == 'TBO':
                    final.bracket['rounds'][0][i]['participants'][1]['participant'] = j.get('participant')
                    print(2)
                    break
                
               
                elif final.bracket['rounds'][0][len(final.bracket['rounds'][0]) // 2 + i].get('participants')[1].get('participant') == 'TBO':
                    final.bracket['rounds'][0][len(final.bracket['rounds'][0]) // 2 + i]['participants'][1]['participant'] = j.get('participant')
                    print(4)
                    break

            if len(final.bracket['rounds'][0]) // 2 == 0:
                if final.bracket['rounds'][0][0].get('participants')[0].get('participant') == 'TBO':
                    final.bracket['rounds'][0][0]['participants'][0]['participant'] = j.get('participant')
                    break

                elif final.bracket['rounds'][0][0].get('participants')[1].get('participant') == 'TBO':
                    final.bracket['rounds'][0][0]['participants'][1]['participant'] = j.get('participant')
                    break
                
            for row in final.bracket['table']:
                if row.get('participant') == "TBO":
                    row['participant'] = j.get('participant')
                    break

        final.save()

    @staticmethod
    def set_match_score(match: dict, bracket: list) -> None:
        
        round_id = match.get('round_id')
        match_id = match.get('match_id')
        prev_match_state = bracket.get('rounds')[round_id][match_id]

        current_first_res = int(match.get('participants')[0].get('score'))
        current_second_res = int(match.get('participants')[1].get('score'))
        
        first_partic_res = current_first_res - int(prev_match_state.get('participants')[0].get('score'))
        second_partic_res = current_second_res - int(prev_match_state.get('participants')[1].get('score'))
        
       
        # generators search participant in table O(n)
        first_partic = next(partic for partic in bracket.get('table') if partic['participant'] == match.get('participants')[0].get('participant'))
        if match.get('participants')[1].get('participant') != 'None':
            second_partic = next(partic for partic in bracket.get('table') if partic['participant'] == match.get('participants')[1].get('participant'))
        else:
            second_partic = {'match_w_l': [0, 0], 'loose': 0, 'win': 0, 'draw': 0}
        # add match scoore to table 
        first_partic.get('match_w_l')[0] += first_partic_res
        first_partic.get('match_w_l')[1] += second_partic_res
        second_partic.get('match_w_l')[0] += second_partic_res
        second_partic.get('match_w_l')[1] += first_partic_res
        
        # S -> P
        if match.get('state') == "PLAYED" and prev_match_state.get('state') == 'SCHEDULED':
            match['state'] = "PLAYED"
            if current_first_res > current_second_res:
                # add res in table
                first_partic['win'] += 1
                second_partic['loose'] += 1
            elif current_second_res > current_first_res:
                # add res in table
                second_partic['win'] += 1
                first_partic['loose'] += 1
            elif current_second_res == 0 and match.get('participants')[0].get('score') == 0:
                if current_first_res - current_second_res < 0:
                    second_partic['win'] += 1
                    first_partic['loose'] += 1
                elif current_first_res - current_second_res > 0:
                    first_partic['win'] += 1
                    second_partic['loose'] += 1
                else:
                    second_partic['draw'] += 1
                    first_partic['draw'] += 1
            else:
                second_partic['draw'] += 1
                first_partic['draw'] += 1
        # P -> S
        elif match.get('state') == "SCHEDULED" and prev_match_state.get('state') == 'PLAYED':
            match['state'] = "SCHEDULED"
            if  prev_match_state.get('participants')[0]['isWinner'] == True:
                # add res in table
                first_partic['win'] -= 1
                second_partic['loose'] -= 1
            elif prev_match_state.get('participants')[1]['isWinner'] == True:
                # add res in table
                second_partic['win'] -= 1
                first_partic['loose'] -= 1
            else:
                second_partic['draw'] -= 1
                first_partic['draw'] -= 1
        # P -> P
        elif match.get('state') == "PLAYED" and prev_match_state.get('state') == 'PLAYED':
            # d -> 1
            if prev_match_state.get('participants')[0]['isWinner'] == False and \
                prev_match_state.get('participants')[1]['isWinner'] == False and match.get('participants')[0]['isWinner']==True:
                first_partic['win'] += 1
                first_partic['draw'] -= 1
                second_partic['draw'] -= 1
                second_partic['loose'] += 1
            # d -> 2
            elif prev_match_state.get('participants')[0]['isWinner'] == False and \
                prev_match_state.get('participants')[1]['isWinner'] == False and match.get('participants')[1]['isWinner']==True:
                second_partic['win'] += 1
                second_partic['draw'] -= 1
                first_partic['draw'] -= 1
                first_partic['loose'] += 1
            # 2 -> 1
            elif match.get('participants')[0]['isWinner'] == True and prev_match_state.get('participants')[0]['isWinner']==False:
                first_partic['win'] += 1
                first_partic['loose'] -= 1
                second_partic['loose'] += 1
                second_partic['win'] -= 1
            # 1 -> 2
            elif match.get('participants')[1]['isWinner'] == True and prev_match_state.get('participants')[1]['isWinner']==False:
                second_partic['win'] += 1
                second_partic['loose'] -= 1
                first_partic['loose'] += 1
                first_partic['win'] -= 1
            # 1 -> d
            elif match.get('participants')[0]['isWinner'] == False and \
                match.get('participants')[1]['isWinner'] == False and prev_match_state.get('participants')[0]['isWinner']==True:
                first_partic['win'] -= 1
                first_partic['draw'] += 1
                second_partic['draw'] += 1
                second_partic['loose'] -= 1
            # 2 -> d
            elif match.get('participants')[0]['isWinner'] == False and \
                match.get('participants')[1]['isWinner'] == False and prev_match_state.get('participants')[1]['isWinner']==True:
                second_partic['win'] -= 1
                second_partic['draw'] += 1
                first_partic['draw'] += 1
                first_partic['loose'] -= 1
        
        # get score from table
        win_scoore = bracket.get('points').get('win')
        loos_scoore = bracket.get('points').get('loss')
        draw_scoore = bracket.get('points').get('draw')

        # calc for participants
        first_partic['scores'] = first_partic['draw']*draw_scoore + first_partic['win']*win_scoore + first_partic['loose']*loos_scoore
        second_partic['scores'] = second_partic['draw']*draw_scoore + second_partic['win']*win_scoore + second_partic['loose']*loos_scoore

        # delete round and match id
        match.pop('round_id')
        match.pop('match_id')
        
        bracket.get('rounds')[round_id][match_id] = match

        
        round_end = True
        cur_round = bracket.get('rounds')[round_id]
        
        # O(log(n)) check all games in found played
        for i in cur_round:
            if i.get('state') != 'PLAYED':
                round_end = False
                break

        # buchholz 
        # O(n/2 * log(n))
        for count, i in enumerate(bracket.get('rounds')[0:round_id+1]):
            for j in i:
                # O(n)
                first = next(partic for partic in bracket.get('table') if partic['participant'] == j.get('participants')[0].get('participant'))
                if j.get('participants')[1].get('participant') != 'None':
                    second = next(partic for partic in bracket.get('table') if partic['participant'] == j.get('participants')[1].get('participant'))
                    if count == 0:
                        first['buchholz'] = 0
                        second['buchholz'] = 0
                    first['buchholz'] += second['scores']
                    second['buchholz'] += first['scores']

                elif count == 0:
                    first['buchholz'] = 0


        # new round
        if round_end and round_id!= len(bracket.get('rounds')) - 1 and bracket.get('rounds')[round_id+1][0].get('participants')[0].get('participant') == 'TBO':
            parts = sorted(bracket.get('table'), reverse=True, key=lambda partic: partic.get('scores'))
            if len(parts) % 2 == 1:
                parts.append({"id": secrets.token_hex(16), "participant": "None", "match_w_l": [0, 0], "draw": 0, "win": 0, "loose": 0, "scores": 0})
            #O(n)
            round = []
            while len(parts) > 0:
                previously_played = []
                #O(n/2 * log(n))
                for i in bracket.get('rounds'):
                    for j in i:
                        if parts[0].get('participant') == j.get('participants')[0].get('participant'):
                            previously_played.append(j.get('participants')[1].get('participant'))
                        elif parts[0].get('participant') == j.get('participants')[1].get('participant'):
                            previously_played.append(j.get('participants')[0].get('participant'))
                #O(n)
                for index in range(1, len(parts)):
                    if parts[index].get('participant') not in previously_played:

                        t1 = {'id': parts[0].get('id'), 'score': 0, 'participant': parts[0].get('participant'), 'isWinner': False}
                        parts.pop(0)
                        t2 = {'id': parts[index-1].get('id'), 'score': 0, 'participant': parts[index-1].get('participant'), 'isWinner': False}
                        parts.pop(index-1)
                        round.append({
                            "id": bracket.get('rounds')[round_id+1][0].get('id'),
                            "startTime": bracket.get('rounds')[round_id+1][0].get('startTime'),
                            "state": bracket.get('rounds')[round_id+1][0].get('state'),
                            "participants": [
                                t1,
                                t2
                            ]
                            })
                        break
            bracket.get('rounds')[round_id+1] = round
        
    
    def swiss_number_of_rounds(self) -> int:
        return math.ceil(math.log2(len(self.participants)))

    def append_participant(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'score': 0,
                    'participant': f"{name}",
                    'isWinner': False
                }
    
    def append_participant_to_table(self, name: str) -> dict:
        return  {
                    'id': secrets.token_hex(16),
                    'participant': f"{name}",
                    'match_w_l': [0, 0],
                    'draw': 0,
                    'win': 0,
                    'loose': 0,
                    'scores': 0,
                    'buchholz': 0,
                }

    def create_swiss_bracket(self) -> dict:  
        swiss_bracket = []
        if len(self.participants) % 2 == 1: 
            self.participants = self.participants + [self.append_participant('None')] 
        
        # O(log(n))
        for i in range(self.swiss_number_of_rounds()):
            round = []
            # O(n / 2)
            for j in range(math.ceil(len(self.participants) / 2)):
                if i == 0:
                    t1 = self.participants[j]
                    t2 = self.participants[len(self.participants) // 2 + j]
                    round.append({
                        "id": secrets.token_hex(16),
                        "startTime": f"{self.time_managment.get('start_time')}",
                        "state": "SCHEDULED",
                        "participants": [
                            t1,
                            t2
                        ]
                        })
                else:   
                    round.append({
                        "id": secrets.token_hex(16),
                        "startTime": f"{self.time_managment.get('start_time')}",
                        "state": "SCHEDULED",
                        "participants": [
                            self.append_participant('TBO'),
                            self.append_participant('TBO')
                        ]
                        })
            swiss_bracket.append(round)

        # Time managment
        if self.time_managment.get('time_managment'):
            last_time = self.time_managment.get('start_time')
            for counter, round in enumerate(swiss_bracket):
                if counter == 0:
                    for i in range(self.time_managment.get('mathes_same_time'), len(round), self.time_managment.get('mathes_same_time')):
                        for game in round[i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                else:
                     for i in range(0, len(round), self.time_managment.get('mathes_same_time')):
                        for game in round[i:i+self.time_managment.get('mathes_same_time')]:
                            game['startTime'] = f"{last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))}"
                        last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('avg_game_time')*self.time_managment.get('max_games_number'))
                last_time = last_time + datetime.timedelta(minutes=self.time_managment.get('break_between'))

        return {'rounds': swiss_bracket, 'table': self.match_table, 'points': self.points}