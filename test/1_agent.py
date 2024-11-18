from agent import Agent
import random

class IntelligentAgent(Agent):
    '''An agent that uses deduction and reasoning to make decisions'''

    def __init__(self, name='IntelligentAgent'):
        '''
        Initializes the agent.
        '''
        self.name = name

    def new_game(self, number_of_players, player_number, spy_list):
        '''
        Initializes the game state for a new game.
        '''
        self.num_players = number_of_players
        self.player_number = player_number
        self.spies = set(spy_list)

        self.num_spies = super().spy_count[self.num_players]

        # Initialize suspicion levels for each player
        self.suspicion = [0.5] * self.num_players  # Start with neutral suspicion
        self.suspicion[self.player_number] = 0.0    # We know we are not a spy

        # Keep track of game progress
        self.failed_missions = 0
        self.successful_missions = 0
        self.players = set(range(self.num_players))

        # Keep a history of missions and votes
        self.missions = []  # List of mission outcomes

    def is_spy(self, player_num=None):
        '''
        Returns True if the given player is a spy.
        '''
        if player_num is None:
            return self.player_number in self.spies
        return player_num in self.spies

    def propose_mission(self, team_size, betrayals_required=1):
        '''
        Propose a mission team.
        '''
        if self.is_spy():
            # As a spy, include at least one spy on the mission
            team = [self.player_number]
            other_spies = list(self.spies - {self.player_number})
            while len(team) < team_size and other_spies:
                spy = random.choice(other_spies)
                team.append(spy)
                other_spies.remove(spy)
            # Fill the rest with random players
            while len(team) < team_size:
                player = random.choice(list(self.players - set(team)))
                team.append(player)
        else:
            # As a resistance member, choose least suspicious players
            # Exclude self from suspicion list
            suspicion_list = [(self.suspicion[player], player) for player in self.players if player != self.player_number]
            # Sort players by suspicion (least to most)
            suspicion_list.sort()
            team = [self.player_number]
            for _, player in suspicion_list:
                if len(team) < team_size:
                    team.append(player)
                else:
                    break
            # If not enough players, fill randomly
            while len(team) < team_size:
                player = random.choice(list(self.players - set(team)))
                team.append(player)
        random.shuffle(team)
        return team

    def vote(self, mission, proposer, betrayals_required=1):
        '''
        Vote for a mission team.
        '''
        if self.is_spy():
            # Spies approve missions with spies, reject others
            spy_on_mission = any(player in self.spies for player in mission)
            return spy_on_mission
        else:
            # Calculate average suspicion of team
            team_suspicion = sum(self.suspicion[player] for player in mission) / len(mission)
            # Approve mission if team suspicion is low
            return team_suspicion < 0.5


    def vote_outcome(self, mission, proposer, votes):
 
        # 所有未在 votes 列表中的玩家被视为投了反对票
        players_who_rejected = set(self.players) - set(votes)
        
        # 增加投赞成票但任务被否决的玩家的怀疑度
        if len(votes) < len(self.players) / 2:  # 如果投票未通过
            for player in votes:
                self.suspicion[player] += 0.05
        
        # 如果投反对票，怀疑他们可能是间谍
        for player in players_who_rejected:
            self.suspicion[player] += 0.02

        # 确保怀疑度在 [0.0, 1.0] 范围内
        self.suspicion = [min(max(s, 0.0), 1.0) for s in self.suspicion]


    def betray(self, mission, proposer, betrayals_required=1):
        '''
        Decide whether to betray the mission.
        '''
        if not self.is_spy():
            return False  # Resistance members cannot betray

        # Spies decide strategically when to betray
        spies_on_mission = [player for player in mission if player in self.spies]
        # If spies need one more fail to win, betray
        if self.failed_missions == 2:
            return True
        # If only one spy is needed to fail the mission, betray
        if len(spies_on_mission) <= betrayals_required:
            return True
        # Randomize to avoid detection
        return random.random() < 0.5

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        '''
        Process the outcome of the mission.
        '''
        # Record mission outcome
        self.missions.append({
            'team': mission,
            'proposer': proposer,
            'betrayals': num_betrayals,
            'success': mission_success
        })

        # Update suspicion levels based on mission outcome
        if num_betrayals > 0:
            # Increase suspicion for team members (excluding self)
            for player in mission:
                if player != self.player_number:
                    self.suspicion[player] += 0.1 * num_betrayals
        else:
            # Decrease suspicion for team members
            for player in mission:
                if player != self.player_number:
                    self.suspicion[player] -= 0.05

        # Ensure suspicion levels stay within [0, 1]
        self.suspicion = [min(max(s, 0.0), 1.0) for s in self.suspicion]

    def round_outcome(self, rounds_complete, missions_failed):
        '''
        Update the number of successful and failed missions.
        '''
        self.failed_missions = missions_failed
        self.successful_missions = rounds_complete - missions_failed

    def game_outcome(self, spies_win, spies):
        '''
        Process the outcome of the game.
        '''
        pass  # No action needed
