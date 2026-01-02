"""
AGT Competition - Student Agent Template
========================================

Team Name: [YOUR TEAM NAME]
Members:
  - [Student 1 Name and ID]
  - [Student 2 Name and ID]
  - [Student 3 Name and ID]

Strategy Description:
[Brief description of your bidding strategy]

Key Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]
"""

from typing import Dict, List

from enum import Enum


class WantLevel(Enum):
    MUST = 1
    WANT = 2
    MEH = 3


class BiddingAgent:
    """
    Your bidding agent for the AGT Auto-Bidding Competition.

    This template provides the required interface and helpful structure.
    Replace the TODO sections with your own strategy implementation.
    """

    def __init__(self, team_id: str, valuation_vector: Dict[str, float],
                 budget: float, opponent_teams: List[str]):
        """
        Initialize your agent at the start of each game.

        Args:
            team_id: Your unique team identifier (UUID string)
            valuation_vector: Dict mapping item_id to your valuation
                Example: {"item_0": 15.3, "item_1": 8.2, ..., "item_19": 12.7}
            budget: Initial budget (always 60)
            opponent_teams: List of opponent team IDs competing in the same arena
                Example: ["Team_A", "Team_B", "Team_C", "Team_D"]
                This helps you track and model each opponent's behavior separately

        Important:
            - This is called once at the start of each game
            - You can initialize any state variables here
            - Pre-compute anything that doesn't change during the game
            - Use opponent_teams to set up per-opponent tracking/modeling
        """
        # Required attributes (DO NOT REMOVE)
        self.team_id = team_id
        self.valuation_vector = valuation_vector
        self.budget = budget
        self.initial_budget = budget
        self.opponent_teams = opponent_teams
        self.utility = 0
        self.items_won = []

        # Game state tracking
        self.rounds_completed = 0
        self.total_rounds = 15  # Always 15 rounds per game

        self.price_average = 9.0  # early assumption for price average

        # Keep history only for debugging/analysis
        self.price_history = []

        # Opponent modeling
        self.opp_budget = {opp: 60.0 for opp in opponent_teams}
        self.opp_mu = {opp: 9.0 for opp in opponent_teams}
        self.opp_wins = {opp: 0 for opp in opponent_teams}
        self.alpha = 0.2  # Needed for computing EMA

        # classify items by preference
        items_sorted = sorted(valuation_vector, key=valuation_vector.get, reverse=True)
        self.items_rank = {item: rank for rank, item in enumerate(items_sorted, start=1)}

    def _update_available_budget(self, item_id: str, winning_team: str,
                                 price_paid: float):
        """
        Internal method to update budget after auction.
        DO NOT MODIFY - This is called automatically by the system.

        Args:
            item_id: ID of the auctioned item
            winning_team: ID of the winning team
            price_paid: Price paid by winner
        """
        if winning_team == self.team_id:
            self.budget -= price_paid
            self.items_won.append(item_id)

    def update_after_each_round(self, item_id: str, winning_team: str,
                                price_paid: float):
        """
        Called after each auction round with public information.
        Use this to update your beliefs, opponent models, and strategy.

        Args:
            item_id: The item that was just auctioned
            winning_team: Team ID of the winner (empty string if no winner)
            price_paid: Price the winner paid (second-highest bid)

        What you learn:
            - Which item was sold
            - Who won it
            - What price they paid (second-highest bid)

        What you DON'T learn:
            - All individual bids
            - Other teams' valuations

        Returns:
            True if update successful (required by system)
        """
        # System updates (DO NOT REMOVE)
        self._update_available_budget(item_id, winning_team, price_paid)

        if winning_team == self.team_id:
            self.utility += (self.valuation_vector[item_id] - price_paid)

        self.rounds_completed += 1
        # Update market EMA, when we are giving higher weight to the last games
        if price_paid and price_paid > 0:
            self.price_history.append(price_paid)
            self.price_average = (1 - self.alpha) * self.price_average + self.alpha * price_paid

        # Subtract price_paid from op's tracked remaining budget.
        if winning_team in self.opp_mu and price_paid and price_paid > 0:
            self.opp_budget[winning_team] -= price_paid
            self.opp_wins[winning_team] += 1
            self.opp_mu[winning_team] = (1 - self.alpha) * self.opp_mu[winning_team] + self.alpha * price_paid

        return True

    def bidding_function(self, item_id: str) -> float:
        my_valuation = float(self.valuation_vector.get(item_id, 0.0))
        if my_valuation <= 0 or self.budget <= 0:
            return 0.0

        rounds_remaining = self.total_rounds - self.rounds_completed
        if rounds_remaining <= 0:
            return 0.0

        # classify how much do we want this item
        rank = self.items_rank[item_id]
        if rank <= 5:
            want = WantLevel.MUST
        elif rank <= 10:
            want = WantLevel.WANT
        else:
            want = WantLevel.MEH

        # Truthful baseline
        suggested_bid = my_valuation

        # Adjust suggested bid according to want level, when we want to stay truthful as we can
        if want == WantLevel.WANT:
            suggested_bid *= 0.9
        elif want == WantLevel.MEH:
            suggested_bid *= 0.8

        # At the end of the game, spend remaining budget more aggressively
        end_of_game = rounds_remaining <= 2
        if end_of_game:
            suggested_bid = min(my_valuation, max(suggested_bid, 0.80 * self.budget))

        # Danger detection - aggressive op exists
        agg_opp_exists = False

        if len(self.price_history) >= 4:
            for opp in self.opponent_teams:
                if self.opp_wins.get(opp, 0) > 0:
                    aggr = self.opp_mu[opp] / self.price_average  # compute how much the opp exceeded the average
                    opp_can_fight = (self.opp_budget[opp] > my_valuation * 0.9)  # opp can win in this round

                    if aggr > 1.2 and opp_can_fight:
                        agg_opp_exists = True
                        break

        # avoid fighting aggressive opponents on low-priority items,
        # but still place a small bid to possibly win cheap or raise their price
        if agg_opp_exists and want == WantLevel.MEH and not end_of_game:
            suggested_bid = 0.3 * my_valuation

        # Keep must items truthful; only prevent wasting budget early on non-must
        if want != WantLevel.MUST and self.rounds_completed < 6:
            # Estimate how much budget we can "afford" per remaining round
            budget_per_round = self.budget / rounds_remaining
            # Avoid spending too much early on non-critical items
            pacing_cap = min(self.budget, 2.0 * budget_per_round)
            # Apply the pacing cap (only if our bid is too high)
            suggested_bid = min(suggested_bid, pacing_cap)

        bid = max(0.0, min(suggested_bid, self.budget))
        return float(bid)
