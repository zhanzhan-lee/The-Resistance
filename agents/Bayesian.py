from agent import Agent
import random

class Bayesian (Agent):
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
        self.spy_count = {5:2, 6:2, 7:3, 8:3, 9:3, 10:4}
        self.number_of_worlds = {5:10, 6:15, 7:35, 8:56, 9:84, 10:210}
        
        # Initialize suspicion levels for each player
        self.suspicion = [0.5] * self.num_players  # Start with neutral suspicion
        self.suspicion[self.player_number] = 0.0    # We know we are not a spy

        # Keep track of game progress
        self.failed_missions = 0
        self.successful_missions = 0
        self.players = set(range(self.num_players))

        # Keep a history of missions and votes
        self.missions = []  # List of mission outcomes
        self.worlds = {}
        self.votecount = 0
        # Initialize all possible worlds (combinations of spies)
        players_except_self = set(range(self.num_players)) - {self.player_number}
        
        # Generate all possible combinations of spies based on the number of spies in the game
        startingChance = 1 / self.number_of_worlds[self.num_players]
        if self.num_spies == 2:
            for x in range(self.num_players):
                for y in range(x+1, self.num_players):
                    self.worlds[(x, y)] = startingChance
        elif self.num_spies == 3:
            for x in range(self.num_players):
                for y in range(x+1, self.num_players):
                    for z in range(y+1, self.num_players):
                        self.worlds[(x, y, z)] = startingChance
        elif self.num_spies == 4:
            for x in range(self.num_players):
                for y in range(x+1, self.num_players):
                    for z in range(y+1, self.num_players):
                        for w in range(z+1, self.num_players):
                            self.worlds[(x, y, z, w)] = startingChance

    def is_spy(self, player_num=None):
        '''
        Returns True if the given player is a spy.
        '''
        if player_num is None:
            return self.player_number in self.spies
        return player_num in self.spies

    def calculate_probabilities(self):
        '''
        Calculates and sorts the suspiciousness of each player using values from self.worlds
        Returns a dictionary mapping suspiciousness to player numbers and the average suspiciousness
        '''
        orderedProbs = {}  # Dictionary to store suspicion probabilities
        for player in range(self.num_players):  # Loop through all players
            temp = []  # Temp list to hold probabilities for player being a spy
            for combo, prob in self.worlds.items():  # Loop through all possible worlds
                if player in combo:
                    temp.append(prob)
            orderedProbs[player] = sum(temp) / len(temp)  # Average suspicion in worlds

        orderedProbs = {player: prob for player, prob in sorted(orderedProbs.items(), key=lambda item: item[1], reverse=True)}
        total_suspicion = sum(orderedProbs.values())
        if total_suspicion > 0:
            average_suspicion = total_suspicion / len(orderedProbs)
        else:
            average_suspicion = 0.5

        return orderedProbs, average_suspicion

    def propose_mission(self, team_size, betrayals_required=1):
        '''
        Propose a mission team based on historical voting and mission success data.
        '''
        # Historical analysis of proposals
        historical_proposals = {i: 0 for i in range(self.num_players)}  # Track number of times each player proposed a mission
        historical_success = {i: 0 for i in range(self.num_players)}  # Track how successful each player's missions were

        for mission in self.missions:
            for player in mission['team']:
                historical_proposals[player] += 1
                if mission['success']:
                    historical_success[player] += 1

        # Calculate suspicion based on historical data
        for i in range(self.num_players):
            if historical_proposals[i] > 0:
                success_rate = historical_success[i] / historical_proposals[i]
                if success_rate < 0.5:  # If the player's missions tend to fail
                    self.suspicion[i] += 0.1

        # Now proceed with the normal proposal logic
        team = []
        probabilities, average = self.calculate_probabilities()  # Get suspicion levels

        # Always include self in mission proposal
        team.append(self.player_number)
        team_size -= 1

        if self.is_spy():
            # Spy: include other spies while avoiding suspicion
            team.append(self.player_number)
            other_spies = list(self.spies - {self.player_number})
            while len(team) < team_size and other_spies:
                team.append(other_spies.pop())
            while len(team) < team_size:
                player = random.choice(list(self.players - set(team)))
                team.append(player)
        else:
            # Resistance: Choose least suspicious players
            team.append(self.player_number)
            sorted_players = sorted(probabilities.items(), key=lambda x: x[1])
            for player, _ in sorted_players:
                if len(team) < team_size and player != self.player_number:
                    team.append(player)
        random.shuffle(team)
        return team

    def vote(self, mission, proposer, betrayals_required=1):
        '''
        Vote for a mission team, with randomization for resistance members to avoid predictability.
        '''
        probabilities, average = self.calculate_probabilities()  # Get updated suspicion levels

        if not self.is_spy():
            # Introduce random behavior for resistance members
            if random.random() < 0.2:  # 20% chance to vote randomly
                return random.choice([True, False])

            # Regular voting behavior based on suspicion levels
            if probabilities[proposer] > average or any(probabilities[player] > average for player in mission):
                return False
            return True
        else:
            # Spies: Approve missions with spies on them
            return any(player in self.spies for player in mission)

    def vote_outcome(self, mission, proposer, votes):
        '''
        Process the outcome of the vote and update failed vote count.
        '''
        if len(votes) >= self.num_players / 2:
            self.votecount += 1
        else:
            self.votecount = 0

    def betray(self, mission, proposer, betrayals_required=1):
        '''
        Decide whether to betray the mission.
        '''
        if not self.is_spy():
            return False  # Resistance members cannot betray

        spies_on_mission = [player for player in mission if player in self.spies]
        if self.failed_missions == 2:
            return True  # Spy needs one more failure to win
        if len(spies_on_mission) <= betrayals_required:
            return True
        return random.random() < 0.5  # Add some randomness to avoid detection

    def mission_outcome(self, mission, proposer, num_betrayals, mission_success):
        '''
        Process the outcome of the mission.
        '''
        self.missions.append({
            'team': mission,
            'proposer': proposer,
            'betrayals': num_betrayals,
            'success': mission_success
        })

        # Update suspicion levels based on mission outcome
        if not mission_success:
            # Failed mission: Increase suspicion of all team members
            for player in mission:
                if player != self.player_number:
                    self.suspicion[player] += 0.15 * num_betrayals  # Increase suspicion more aggressively
                    if self.missions.count({'team': mission, 'success': False}) > 1:
                        # Extra suspicion for repeated failures
                        self.suspicion[player] += 0.1
        else:
            # Successful mission: Decrease suspicion for team members
            for player in mission:
                if player != self.player_number:
                    self.suspicion[player] -= 0.05

        # Ensure suspicion levels stay within [0, 1]
        self.suspicion = [min(max(s, 0.0), 1.0) for s in self.suspicion]

    def round_outcome(self, rounds_complete, missions_failed):
        '''
        Update the number of successful and failed missions.
        Also dynamically adjust the agent's strategy based on game progress.
        '''
        self.failed_missions = missions_failed
        self.successful_missions = rounds_complete - missions_failed

        # Dynamic strategy adjustment
        if rounds_complete < 3:
            # Early stages: be conservative, reduce suspicion growth
            for i in range(self.num_players):
                self.suspicion[i] *= 0.9
        else:
            # Later stages: be more aggressive
            for i in range(self.num_players):
                self.suspicion[i] *= 1.1

    def game_outcome(self, spies_win, spies):
        '''
        Process the outcome of the game.
        '''
        pass  # No action needed
