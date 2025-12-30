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
        # Examples:

        # Track price history
        # if price_paid > 0:
        #     self.price_history.append(price_paid)

        # Track opponent performance
        # if winning_team and winning_team != self.team_id:
        #     self.opponent_wins[winning_team] = \
        #         self.opponent_wins.get(winning_team, 0) + 1

        # Update beliefs about market competitiveness
        # if self.price_history:
        #     self.avg_market_price = sum(self.price_history) / len(self.price_history)

        # Bayesian belief updates
        # if winning_team and price_paid > 0:
        #     # Update beliefs about winner's valuation
        #     # They bid at least price_paid + epsilon
        #     pass

        return True

    def bidding_function(self, item_id: str) -> float:
        """
        MAIN METHOD: Decide how much to bid for the current item.
        This is called once per auction round.

        Args:
            item_id: The item being auctioned (e.g., "item_7")

        Returns:
            float: Your bid amount
                - Must be >= 0
                - Should be <= your current budget
                - Bids over budget are automatically capped
                - Return 0 to not bid

        Important:
            - You have 2 seconds maximum to return
            - Timeout or error = bid of 0
            - This is a SECOND-PRICE auction: winner pays second-highest bid
            - Budget does NOT carry over between games

        Strategy Considerations:
            1. Budget Management: How much to spend now vs save for later?
            2. Item Value: Is this item worth competing for?
            3. Competition: How competitive will this auction be?
            4. Game Progress: Are we early or late in the game?
        """
        # Get your valuation for this item
        my_valuation = self.valuation_vector.get(item_id, 0)

        # Early exit if no value or no budget
        if my_valuation <= 0 or self.budget <= 0:
            return 0.0

        # Calculate rounds remaining
        rounds_remaining = self.total_rounds - self.rounds_completed
        if rounds_remaining > 0:
            # ----------------------------
            # 1) Preference tier (must/want/meh) based on our valuation rank
            # ----------------------------
            r = self.rank.get(item_id, 1000)
            if r <= 3:
                want = "must"
                shade = 0.90
            elif r <= 7:
                want = "want"
                shade = 0.75
            else:
                want = "meh"
                shade = 0.55

            bid_wanted = my_valuation * shade

            # ----------------------------
            # 2) End-game: spend more aggressively in last rounds
            # ----------------------------
            if rounds_remaining <= 3:
                # In the last rounds, stop being too conservative.
                # Bid close to value but still capped by remaining budget.
                bid_wanted = min(my_valuation, max(bid_wanted, 0.75 * self.budget))

            # ----------------------------
            # 3) Detect "danger": aggressive opponent + still has meaningful budget
            # ----------------------------
            danger = False
            market = max(1e-6, float(self.market_avg))  # avoid division by zero

            # Don't trust aggressiveness until we have enough market observations
            if len(self.price_history) >= self.min_market_obs_for_danger:
                for opp in self.opponent_teams:
                    if self.opp_wins.get(opp, 0) == 0:
                        continue

                    # Aggressiveness ratio: opponent avg win-price / market avg
                    aggr = self.opp_mu[opp] / market

                    # Budget check:
                    # Use a softer threshold than "opp_budget > bid_wanted" because in 2nd-price
                    # they don't necessarily pay their full bid. We just want to know if they're
                    # still "able to fight".
                    opp_can_fight = self.opp_budget[opp] > max(market, 0.9 * bid_wanted)

                    if aggr > 1.2 and opp_can_fight:
                        danger = True
                        break

            # ----------------------------
            # 4) Reaction to danger
            # ----------------------------
            if danger:
                if want == "must":
                    bid_wanted = min(my_valuation, bid_wanted * 1.12)
                elif want == "want":
                    bid_wanted = min(my_valuation, bid_wanted * 1.06)
                else:
                    # Not worth fighting aggressive opponents on low-priority items
                    bid_wanted = 0.0

            # ----------------------------
            # 5) Soft pacing cap (only for must/want)
            # ----------------------------
            # This is a *soft* safety belt: it prevents blowing the whole budget early,
            # but still allows higher bids for important items.
            if want != "meh" and rounds_remaining > 0:
                budget_per_round = self.budget / rounds_remaining
                progress = self.rounds_completed / self.total_rounds  # 0..1
                pacing_mult = 3.0 + 2.0 * progress  # 3x early -> 5x late
                pacing_cap = min(self.budget, pacing_mult * budget_per_round)
                bid_wanted = min(bid_wanted, pacing_cap)

            # Ensure bid is valid (non-negative and within budget)
            bid = max(0.0, min(bid_wanted, self.budget))
            return float(bid)

        # ============================================================
        # TODO: IMPLEMENT YOUR BIDDING STRATEGY HERE
        # ============================================================

        # Example Strategy 1: Simple Truthful Bidding
        # bid = my_valuation

        # Example Strategy 2: Budget Pacing
        # budget_per_round = self.budget / rounds_remaining
        # bid = min(my_valuation, budget_per_round * 1.5)

        # Example Strategy 3: Value-Based Shading
        # if my_valuation > 12:
        #     bid = my_valuation * 0.9  # High value: bid aggressively
        # elif my_valuation > 8:
        #     bid = my_valuation * 0.7  # Medium value: bid moderately
        # else:
        #     bid = my_valuation * 0.5  # Low value: bid conservatively

        # Example Strategy 4: Adaptive Based on Observations
        # if hasattr(self, 'price_history') and self.price_history:
        #     avg_price = sum(self.price_history) / len(self.price_history)
        #     if my_valuation > avg_price * 1.2:
        #         bid = my_valuation * 0.85  # Competitive item
        #     else:
        #         bid = my_valuation * 0.6   # Less competitive
        # else:
        #     bid = my_valuation * 0.7

        # Example Strategy 5: End-Game Aggression
        # progress = self.rounds_completed / self.total_rounds
        # if progress > 0.7:  # Last 30% of game
        #     bid = my_valuation * 0.9  # More aggressive
        # else:
        #     bid = my_valuation * 0.7

        # PLACEHOLDER: Simple truthful bidding (REPLACE THIS!)
        bid = my_valuation * 0.8  # Bid 80% of valuation

        # ============================================================
        # END OF STRATEGY IMPLEMENTATION
        # ============================================================

        # Ensure bid is valid (non-negative and within budget)
        bid = max(0.0, min(bid, self.budget))

        return float(bid)

    # ================================================================
    # OPTIONAL: Helper methods for your strategy
    # ================================================================

    # TODO: Add any helper methods you need
    # Examples:

    # def _classify_item_value(self, valuation: float) -> str:
    #     """Classify item as high, medium, or low value"""
    #     if valuation > self.high_value_threshold:
    #         return "high"
    #     elif valuation > self.low_value_threshold:
    #         return "medium"
    #     else:
    #         return "low"

    # def _estimate_competition(self, item_id: str) -> float:
    #     """Estimate how competitive this auction will be"""
    #     # Based on price history, opponent wins, etc.
    #     pass

    # def _calculate_budget_constraint(self) -> float:
    #     """Calculate maximum bid based on budget constraints"""
    #     rounds_remaining = self.total_rounds - self.rounds_completed
    #     return self.budget / max(1, rounds_remaining) * 2.0

    # def _should_bid_aggressively(self, valuation: float) -> bool:
    #     """Decide if we should bid aggressively for this item"""
    #     # Based on game state, valuation, budget, etc.
    #     pass


# ====================================================================
# NOTES AND TIPS
# ====================================================================

# 1. Second-Price Auction Theory:
#    - In standard Vickrey auctions, truthful bidding is optimal
#    - With budget constraints, this changes! You need strategy
#    - Winner pays second-highest bid, not their own bid

# 2. Budget Management:
#    - You have 60 units for 15 rounds
#    - Budget does NOT carry between games
#    - Spending all budget early is risky
#    - Saving too much budget is wasteful

# 3. Information Use:
#    - Learn from observed prices
#    - Track which opponents are winning
#    - Identify competitive vs non-competitive items
#    - Update your strategy as game progresses

# 4. Common Strategies:
#    - Truthful: Bid your valuation (baseline)
#    - Shading: Bid less than valuation to save budget
#    - Pacing: Limit spending per round
#    - Adaptive: Learn from observations and adjust

# 5. Testing:
#    - Use the simulator extensively: python simulator.py --your-agent ...
#    - Test with different seeds for consistency
#    - Aim for >20% win rate against examples
#    - Aim for >10 average utility

# 6. Performance:
#    - Keep computations fast (< 1 second per bid)
#    - Pre-compute what you can in __init__
#    - Avoid complex loops in bidding_function
#    - Test execution time regularly

# 7. Debugging:
#    - Add print statements (captured in logs)
#    - Use simulator with --verbose flag
#    - Check that bids are reasonable (0 to budget)
#    - Verify budget doesn't go negative (system prevents this)

# Good luck! 🏆
