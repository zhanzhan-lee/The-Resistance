from agent import Agent
import itertools
import random

class Byesian_Heuristic(Agent):        
    def __init__(self, name='Byesian_Heuristic'):
        self.name = name
        self.spy_count = {5:2, 6:2, 7:3, 8:3, 9:3, 10:4}
        self.combo_count = {5:10, 6:15, 7:35, 8:56, 9:84, 10:210}
        self.suspicion = []

    def new_game(self, number_of_players, player_number, spy_list):
        self.num_players = number_of_players
        self.player_number = player_number
        self.spies = set(spy_list)
        self.num_spies = self.spy_count[self.num_players]

        # Initialize suspicion for each player
        self.suspicion = [0.5] * self.num_players  
        self.suspicion[self.player_number] = 0.0  

        # Possible combinations of spy groups
        self.combination = {}
        players_except_self = set(range(self.num_players)) - {self.player_number}
        startingChance = 1 / self.combo_count[self.num_players]
        for combo in itertools.combinations(range(self.num_players), self.num_spies):
            self.combination[combo] = startingChance

        self.mission_history = []
        self.failed_missions = 0
        self.successful_missions = 0

        self.vote_history = []
        self.mission_outcomes = {}
        self.mission_count = 0 



    def is_spy(self, player_num=None):
        return self.player_number in self.spies if player_num is None else player_num in self.spies

    def calculate_probabilities(self):
        orderedProbs = {}
        for player in range(self.num_players):
            temp = [prob for combo, prob in self.combination.items() if player in combo]
            orderedProbs[player] = sum(temp) / len(temp) if temp else 0.5
        orderedProbs = {k: v for k, v in sorted(orderedProbs.items(), key=lambda item: item[1], reverse=True)}
        total_suspicion = sum(orderedProbs.values())
        average_suspicion = total_suspicion / len(orderedProbs) if total_suspicion else 0.5
        return orderedProbs, average_suspicion

    def propose_mission(self, team_size, betrayals_required):
        probabilities, average = self.calculate_probabilities()
        team = [self.player_number]  # Always include self
        sorted_players = list(probabilities.keys())

        if self.is_spy():
            for player in sorted_players[::-1]:
                if player in self.spies and len(team) < betrayals_required:
                    team.append(player)
            for player in sorted_players:
                if player not in self.spies and len(team) < team_size:
                    team.append(player)
        else:
            # Select players who have succeeded in past missions and have low suspicion
            potential_team = [p for p in sorted_players if p != self.player_number]
            potential_team = sorted(potential_team, key=lambda x: self.suspicion[x])

            while len(team) < team_size:
                team.append(potential_team.pop(0))

        random.shuffle(team)  
        return team

    def vote(self, mission, proposer, betrayals_required):
        probabilities, average = self.calculate_probabilities()
        
        if not self.is_spy():
            # Resistance logic: vote against if the proposer or team members are highly suspicious
            if probabilities[proposer] > average or any(probabilities[player] > average for player in mission):
                return False
            return True
        else:
            # Spy logic: support missions with spies or where spies can influence the result
            return any(player in self.spies for player in mission)

    def betray(self, mission, proposer, betrayals_required):
        if not self.is_spy():
            return False
        
        # Spy betrayal logic: spy may choose to betray based on game state and probability
        spies_on_mission = [player for player in mission if player in self.spies]
        if self.failed_missions == 2 or len(spies_on_mission) <= betrayals_required:
            return True
        # Random element to avoid suspicion
        return random.random() < 0.5

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        self.mission_count += 1  
        self.mission_history.append({'team': mission, 'proposer': proposer, 'betrayals': num_betrayals, 'success': mission_success})
        
        #future decisions
        self.mission_outcomes[self.mission_count] = {
            'team': mission,
            'proposer': proposer,
            'num_betrayals': num_betrayals,
            'success': mission_success
        }
        
        if num_betrayals > 0:
            fail_prob = {combo: len(list(itertools.combinations(set(combo) & set(mission), num_betrayals))) / len(list(itertools.product([True, False], repeat=len(mission)))) for combo in self.combination}
            total_fail = sum(fail_prob[combo] * prob for combo, prob in self.combination.items())
            for combo in fail_prob:
                self.combination[combo] = fail_prob[combo] * self.combination[combo] / total_fail
        self.update_suspicion()

    def update_suspicion(self):
        suspicion = [0.0] * self.num_players
        for combo, prob in self.combination.items():
            for spy in combo:
                suspicion[spy] += prob
        total_suspicion = sum(suspicion)
        self.suspicion = [s / total_suspicion for s in suspicion] if total_suspicion else [0.5] * self.num_players
        self.suspicion[self.player_number] = 0.0

    def round_outcome(self, rounds_complete, missions_failed):
        self.failed_missions = missions_failed
        self.successful_missions = rounds_complete - missions_failed

    def game_outcome(self, spies_win, spies):
        pass  
