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

        # ----------------------------
        # Market learning (global)
        # ----------------------------
        # Use EMA instead of simple average: reacts faster to regime changes.
        self.market_avg = 8.0
        self.market_beta = 0.2  # EMA smoothing for market

        # Keep history only for debugging/analysis (optional)
        self.price_history = []

        # ----------------------------
        # Opponent modeling
        # ----------------------------
        # IMPORTANT: We can track opponent remaining budget exactly because:
        # - Everyone starts with 60
        # - Only winner pays, and we observe winner + price_paid each round
        self.opp_budget = {opp: 60.0 for opp in opponent_teams}

        # EMA of price_paid on rounds opponent wins (proxy for aggressiveness)
        self.opp_mu = {opp: 8.0 for opp in opponent_teams}
        self.opp_wins = {opp: 0 for opp in opponent_teams}
        self.alpha = 0.3  # EMA smoothing for opponent win-prices

        # ----------------------------
        # Item preference tiers (must/want/meh)
        # ----------------------------
        items_sorted = sorted(valuation_vector.items(), key=lambda kv: kv[1], reverse=True)
        self.rank = {it: r for r, (it, _) in enumerate(items_sorted, start=1)}  # 1 = highest

        # ----------------------------
        # Safety: avoid trusting models too early
        # ----------------------------
        self.min_market_obs_for_danger = 3  # wait for a few observations before "danger" logic

        # TODO: Add your custom state variables here
        # Examples:
        # self.price_history = []          # Track observed prices
        # self.opponent_wins = {opp: [] for opp in opponent_teams}  # Track which opponents win what
        # self.opponent_bids = {opp: [] for opp in opponent_teams}  # Infer opponent bidding patterns
        # self.beliefs = {opp: {} for opp in opponent_teams}        # Bayesian beliefs per opponent
        # self.high_value_threshold = 12.0  # Classify items
        # self.low_value_threshold = 8.0

        # TODO: Pre-compute any strategy parameters
        # Examples:
        # self.avg_valuation = sum(valuation_vector.values()) / len(valuation_vector)
        # self.max_valuation = max(valuation_vector.values())
        # self.min_valuation = min(valuation_vector.values())

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
        # ----------------------------
        # Update market EMA
        # ----------------------------
        if price_paid and price_paid > 0:
            self.price_history.append(price_paid)  # keep for analysis (optional)
            self.market_avg = (1 - self.market_beta) * self.market_avg + self.market_beta * price_paid

        # ----------------------------
        # Update opponent budgets + aggressiveness EMA
        # ----------------------------
        # If winning_team is in opp_budget, it means it's an opponent (not us).
        # We subtract price_paid from their tracked remaining budget.
        if winning_team in self.opp_budget and price_paid and price_paid > 0:
            self.opp_budget[winning_team] -= price_paid
            self.opp_wins[winning_team] += 1
            self.opp_mu[winning_team] = (1 - self.alpha) * self.opp_mu[winning_team] + self.alpha * price_paid

        # TODO: Implement your learning/adaptation logic here
        return True

    def bidding_function(self, item_id: str) -> float:
        my_valuation = float(self.valuation_vector.get(item_id, 0.0))
        if my_valuation <= 0 or self.budget <= 0:
            return 0.0

        rounds_remaining = self.total_rounds - self.rounds_completed
        if rounds_remaining <= 0:
            return 0.0

        # ----------------------------
        # 1) Preference tier by rank
        # ----------------------------
        r = self.rank.get(item_id, 1000)
        if r <= 3:
            want = "must"
        elif r <= 7:
            want = "want"
        else:
            want = "meh"

        # ----------------------------
        # 2) Truthful baseline
        # ----------------------------
        # Start from truthful bidding (second-price optimal baseline)
        bid_wanted = my_valuation

        # Optional *tiny* shading only to reduce accidental overspending early
        # (still "almost truthful")
        if want == "want":
            bid_wanted *= 0.97
        elif want == "meh":
            bid_wanted *= 0.90

        # ----------------------------
        # 3) End-game: spend remaining budget more aggressively
        # ----------------------------
        if rounds_remaining <= 3:
            # basically truthful, but avoid leaving budget unused
            bid_wanted = min(my_valuation, max(bid_wanted, 0.80 * self.budget))

        # ----------------------------
        # 4) Danger detection (only used to decide if we should "skip meh")
        # ----------------------------
        danger = False
        market = max(1e-6, float(self.market_avg))

        if len(self.price_history) >= self.min_market_obs_for_danger:
            for opp in self.opponent_teams:
                if self.opp_wins.get(opp, 0) == 0:
                    continue

                aggr = self.opp_mu[opp] / market
                opp_can_fight = self.opp_budget[opp] > max(market, 0.9 * my_valuation)

                if aggr > 1.2 and opp_can_fight:
                    danger = True
                    break

        # Reaction: DO NOT distort must items much (stay truthful).
        if danger and want == "meh":
            # If it's not important, don't waste budget fighting aggressive opponents.
            bid_wanted = 0.0

        # ----------------------------
        # 5) Very light pacing cap (only early, only for want/meh)
        # ----------------------------
        # Keep must items truthful; only prevent wasting budget early on non-must.
        if want != "must" and self.rounds_completed < 6:
            budget_per_round = self.budget / max(1, rounds_remaining)
            pacing_cap = min(self.budget, 2.0 * budget_per_round)  # light cap
            bid_wanted = min(bid_wanted, pacing_cap)

        # Final validity
        bid = max(0.0, min(bid_wanted, self.budget))
        return float(bid)

