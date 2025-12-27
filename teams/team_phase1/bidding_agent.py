"""
Team: Phase 1 - Key Strategic Considerations
Members: AGT Competition Team
Strategy: Implements 4 fundamental strategies from STRATEGY_GUIDE.md

Key Features:
1. Budget Pacing - Allocates budget across rounds, increases aggressiveness over time
2. Value Classification - Classifies items into HIGH/MEDIUM/LOW tiers with different bid multipliers
3. Opponent Modeling - Tracks market prices to estimate competitiveness
4. Information Revelation - Learns from opponent wins and price signals
"""

from typing import Dict, List


class BiddingAgent:
    """
    Baseline agent implementing Key Strategic Considerations:
    1. Budget Pacing
    2. Value Classification
    3. Opponent Modeling
    4. Information Revelation
    """
    
    def __init__(self, team_id: str, valuation_vector: Dict[str, float],
                 budget: float, opponent_teams: List[str]):
        """
        Initialize agent at the start of each game.
        
        Args:
            team_id: Your unique team identifier
            valuation_vector: Dict mapping item_id to your valuation
            budget: Initial budget (always 60)
            opponent_teams: List of opponent team IDs in the arena
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
        
        # Strategy 3 & 4: Opponent modeling and information revelation
        self.price_history = []  # Track all observed prices
        self.opponent_wins = {opp: 0 for opp in opponent_teams}  # Count wins per opponent
        self.opponent_items = {opp: [] for opp in opponent_teams}  # Track items won by each opponent
        
        # Strategy 2: Value classification thresholds
        self.high_value_threshold = 11.0  # Items above this are HIGH value
        self.low_value_threshold = 5.0    # Items below this are LOW value
    
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
        Use this to update beliefs, opponent models, and strategy.
        
        Args:
            item_id: The item that was just auctioned
            winning_team: Team ID of the winner (empty string if no winner)
            price_paid: Price the winner paid (second-highest bid)
        
        Returns:
            True if update successful
        """
        # System update (DO NOT REMOVE)
        self._update_available_budget(item_id, winning_team, price_paid)
        
        # Update utility if we won
        if winning_team == self.team_id:
            self.utility += (self.valuation_vector[item_id] - price_paid)
        
        # Strategy 3: Track prices for opponent modeling
        if price_paid > 0:
            self.price_history.append(price_paid)
        
        # Strategy 4: Track opponent wins for information revelation
        if winning_team and winning_team != self.team_id:
            self.opponent_wins[winning_team] += 1
            self.opponent_items[winning_team].append(item_id)
        
        # Update game progress
        self.rounds_completed += 1
        
        return True
    
    def bidding_function(self, item_id: str) -> float:
        """
        Main bidding strategy following decision tree structure.
        
        Args:
            item_id: The item being auctioned
        
        Returns:
            float: Your bid amount (>= 0, <= budget)
        """
        my_valuation = self.valuation_vector.get(item_id, 0)
        rounds_remaining = self.total_rounds - self.rounds_completed
        
        # ===== STEP 1: WANT ITEM? =====
        # Check if item has sufficient value
        if my_valuation < 3.0:
            return 0.0  # BID 0 - not worth it
        
        # ===== STEP 2: CAN AFFORD? =====
        # Check if we have meaningful budget left
        if self.budget < 1.0:
            return 0.0  # BID 0 - can't afford anything meaningful
        
        # ===== STEP 3: BUDGET MANAGER - Calculate allocation =====
        if rounds_remaining > 0:
            budget_per_round = self.budget / rounds_remaining
        else:
            budget_per_round = self.budget
        
        # ===== STEP 4: VALUE CLASSIFIER - Classify item tier =====
        if my_valuation > self.high_value_threshold:
            value_tier = "HIGH"
        elif my_valuation < self.low_value_threshold:
            value_tier = "LOW"
        else:
            value_tier = "MEDIUM"
        
        # ===== STEP 5: OPPONENT TRACKER - Estimate competition =====
        if len(self.price_history) > 0:
            avg_market_price = sum(self.price_history) / len(self.price_history)
        else:
            avg_market_price = 0.0
        
        # ===== STEP 6: ITEM CLASSIFIER - Bayesian category estimation =====
        # (Using valuation distribution to infer item desirability)
        # Items with high valuation likely have high competition
        competition_signal = my_valuation / 15.0  # Normalize (max val ~15)
        
        # ===== STEP 7: BUDGET TRACKER - Check opponent budgets =====
        total_opponent_wins = sum(self.opponent_wins.values())
        opponent_activity = total_opponent_wins / max(1, self.rounds_completed)
        
        # ===== STEP 8: EXPLORE MODE? =====
        # Check if we should explore (low-value item in early game)
        is_early_game = self.rounds_completed < 5
        is_low_value = value_tier == "LOW"
        explore_mode = is_early_game and is_low_value
        
        if explore_mode:
            # Exploratory bid - test market with small bid
            bid = my_valuation * 0.40
        else:
            # ===== STEP 9: COMPETITION LEVEL =====
            # Determine competition level based on market signals
            if avg_market_price > 6.0:
                competition_level = "HIGH"
            elif avg_market_price > 3.0:
                competition_level = "MEDIUM"
            else:
                competition_level = "LOW"
            
            # Apply bidding strategy based on competition level
            if competition_level == "HIGH":
                # High competition: bid valuation * 0.75 or fold
                if value_tier == "LOW":
                    return 0.0  # Fold on low-value items in high competition
                bid = my_valuation * 0.75
            elif competition_level == "MEDIUM":
                # Medium competition: bid valuation * 0.80
                bid = my_valuation * 0.80
            else:  # LOW competition
                # Low competition: bid valuation * 0.60
                bid = my_valuation * 0.60
        
        # ===== STEP 10: GAME PHASE ADJUSTMENT =====
        # Adjust aggressiveness based on game progress
        progress = self.rounds_completed / self.total_rounds
        
        if progress < 0.33:  # Early game (rounds 0-5)
            phase_multiplier = 0.85
        elif progress < 0.67:  # Mid game (rounds 6-10)
            phase_multiplier = 1.0
        else:  # Late game (rounds 11-15)
            phase_multiplier = 1.15
        
        bid = bid * phase_multiplier
        
        # ===== STEP 11: REGRET ADJUSTMENT =====
        # Check if we're missing opportunities (losing too many items we valued)
        my_wins = len(self.items_won)
        win_rate = my_wins / max(1, self.rounds_completed)
        
        # If we're winning less than 20% and have budget, increase aggressiveness
        missing_opportunities = win_rate < 0.20 and self.budget > budget_per_round * 3
        
        if missing_opportunities:
            # Increase bid by 10-15%
            regret_multiplier = 1.10 + (0.05 * (1 - win_rate))  # 1.10 to 1.15
            bid = bid * regret_multiplier
        # else: No adjustment
        
        # ===== STEP 12: APPLY BUDGET CONSTRAINTS =====
        # Don't overspend early - limit to 2.5x budget per round in early game
        if rounds_remaining > 5:
            max_bid_now = budget_per_round * 2.5
            bid = min(bid, max_bid_now)
        
        # Never bid more than valuation (would create negative utility)
        bid = min(bid, my_valuation)
        
        # Never bid more than remaining budget
        bid = min(bid, self.budget)
        
        # Never bid negative
        bid = max(0.0, bid)
        
        # ===== STEP 13: RETURN FINAL BID =====
        return round(bid, 2)

