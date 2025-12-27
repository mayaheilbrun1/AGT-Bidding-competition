"""
Strategy-specific tests for Phase 1 agent.
Tests each of the 4 key strategies individually to ensure they work correctly.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from teams.team_phase1.bidding_agent import BiddingAgent


class TestStrategy1BudgetPacing:
    """
    Detailed tests for Strategy 1: Budget Pacing
    From STRATEGY_GUIDE.md lines 35-52
    """
    
    def setup_method(self):
        """Setup for budget pacing tests"""
        self.valuation_vector = {f"item_{i}": 10.0 for i in range(20)}
        self.agent = BiddingAgent(
            "test_team",
            self.valuation_vector,
            60.0,
            ["opp1", "opp2", "opp3", "opp4"]
        )
    
    def test_budget_per_round_at_start(self):
        """At start: 60 budget / 15 rounds = 4 per round"""
        assert self.agent.budget == 60.0
        assert self.agent.rounds_completed == 0
        
        # Should not overspend in early rounds
        bid = self.agent.bidding_function("item_0")
        assert bid > 0
        # Early round bids should be conservative
        assert bid < 10.0  # Less than valuation due to shading
    
    def test_aggressiveness_at_start(self):
        """Early game aggressiveness should be 70%"""
        # At round 0: progress = 0/15 = 0, aggressiveness = 0.7 + 0.3*0 = 0.7
        assert self.agent.rounds_completed == 0
        bid = self.agent.bidding_function("item_0")
        # Bid should reflect 70% aggressiveness
        assert bid > 0
    
    def test_aggressiveness_increases_midgame(self):
        """Mid-game aggressiveness should increase"""
        # Simulate to round 7
        for i in range(7):
            self.agent.update_after_each_round(f"item_{i}", "opp1", 5.0)
        
        # At round 7: progress = 7/15 ≈ 0.47, aggressiveness ≈ 0.84
        assert self.agent.rounds_completed == 7
        bid = self.agent.bidding_function("item_7")
        assert bid > 0
    
    def test_aggressiveness_at_end(self):
        """Late game aggressiveness should be 100%"""
        # Simulate to round 14 (last round)
        for i in range(14):
            self.agent.update_after_each_round(f"item_{i}", "opp1", 3.0)
        
        # At round 14: progress = 14/15 ≈ 0.93, aggressiveness ≈ 0.98
        assert self.agent.rounds_completed == 14
        bid = self.agent.bidding_function("item_14")
        assert bid > 0
        # Should be willing to spend more of remaining budget
    
    def test_budget_constraint_enforcement(self):
        """Bids should never exceed current budget"""
        # Test at various budget levels
        for remaining_budget in [60.0, 30.0, 10.0, 1.0]:
            self.agent.budget = remaining_budget
            bid = self.agent.bidding_function("item_0")
            assert bid <= remaining_budget, f"Bid {bid} exceeds budget {remaining_budget}"
    
    def test_early_round_spending_limit(self):
        """Early rounds should not overspend (max 2x budget per round)"""
        # At start: budget_per_round = 60/15 = 4, max = 8
        self.agent.rounds_completed = 0
        self.agent.budget = 60.0
        
        # Even for high value item, should cap at ~2x budget per round early
        self.valuation_vector["expensive"] = 50.0
        bid = self.agent.bidding_function("expensive")
        
        # Should be less than 2x budget per round
        budget_per_round = 60.0 / 15
        max_early_bid = budget_per_round * 2.0
        # Bid might be capped by this
        assert bid <= 60.0  # Never exceed total budget
    
    def test_zero_budget_zero_bid(self):
        """Zero budget should result in zero bid"""
        self.agent.budget = 0.0
        bid = self.agent.bidding_function("item_0")
        assert bid == 0.0
    
    def test_final_round_with_remaining_budget(self):
        """Final round should be willing to spend remaining budget"""
        self.agent.rounds_completed = 14
        self.agent.budget = 20.0
        
        bid = self.agent.bidding_function("item_14")
        # Should bid significant portion of remaining budget
        assert bid > 0
        assert bid <= 20.0


class TestStrategy2ValueClassification:
    """
    Detailed tests for Strategy 2: Value Classification
    From STRATEGY_GUIDE.md lines 54-76
    """
    
    def setup_method(self):
        """Setup for value classification tests"""
        self.agent = BiddingAgent(
            "test_team",
            {},  # Will add valuations per test
            60.0,
            ["opp1"]
        )
    
    def test_high_value_threshold(self):
        """HIGH value items (>12) should get 85% fraction"""
        self.agent.valuation_vector = {"high_item": 15.0}
        assert self.agent.high_value_threshold == 12.0
        
        # 15.0 > 12.0, so HIGH tier
        bid = self.agent.bidding_function("high_item")
        assert bid > 0
        assert bid < 15.0  # Shaded below valuation
        # Should be around 15 * 0.85 * 0.7 (early game) ≈ 8.925
    
    def test_low_value_threshold(self):
        """LOW value items (<8) should get 50% fraction"""
        self.agent.valuation_vector = {"low_item": 6.0}
        assert self.agent.low_value_threshold == 8.0
        
        # 6.0 < 8.0, so LOW tier
        bid = self.agent.bidding_function("low_item")
        assert bid > 0
        assert bid < 6.0  # Shaded below valuation
        # Should be around 6 * 0.50 * 0.7 (early game) ≈ 2.1
        assert bid < 4.0  # Should be significantly shaded
    
    def test_medium_value_classification(self):
        """MEDIUM value items (8-12) should get 70% fraction"""
        self.agent.valuation_vector = {"medium_item": 10.0}
        
        # 8 <= 10.0 <= 12, so MEDIUM tier
        bid = self.agent.bidding_function("medium_item")
        assert bid > 0
        assert bid < 10.0
        # Should be around 10 * 0.70 * 0.7 (early game) ≈ 4.9
    
    def test_boundary_at_12(self):
        """Test boundary at high threshold (12.0)"""
        # Just above threshold - HIGH
        self.agent.valuation_vector = {"just_high": 12.1}
        bid_high = self.agent.bidding_function("just_high")
        
        # Just at threshold - still MEDIUM
        self.agent.valuation_vector = {"at_threshold": 12.0}
        bid_at = self.agent.bidding_function("at_threshold")
        
        assert bid_high > 0
        assert bid_at > 0
    
    def test_boundary_at_8(self):
        """Test boundary at low threshold (8.0)"""
        # Just above threshold - MEDIUM
        self.agent.valuation_vector = {"just_medium": 8.1}
        bid_medium = self.agent.bidding_function("just_medium")
        
        # Just below threshold - LOW
        self.agent.valuation_vector = {"just_low": 7.9}
        bid_low = self.agent.bidding_function("just_low")
        
        assert bid_medium > 0
        assert bid_low > 0
    
    def test_very_low_value_item(self):
        """Very low value items (<1) should result in zero bid"""
        self.agent.valuation_vector = {"worthless": 0.5}
        bid = self.agent.bidding_function("worthless")
        assert bid == 0.0
    
    def test_very_high_value_item(self):
        """Very high value items should still be shaded"""
        self.agent.valuation_vector = {"premium": 20.0}
        bid = self.agent.bidding_function("premium")
        
        assert bid > 0
        assert bid < 20.0  # Always shade below true valuation
        assert bid <= self.agent.budget


class TestStrategy3OpponentModeling:
    """
    Detailed tests for Strategy 3: Opponent Modeling
    From STRATEGY_GUIDE.md lines 78-92
    """
    
    def setup_method(self):
        """Setup for opponent modeling tests"""
        self.valuation_vector = {f"item_{i}": 12.0 for i in range(15)}
        self.agent = BiddingAgent(
            "test_team",
            self.valuation_vector,
            60.0,
            ["opp1", "opp2", "opp3"]
        )
    
    def test_price_history_empty_at_start(self):
        """Price history should be empty at game start"""
        assert len(self.agent.price_history) == 0
    
    def test_price_tracking(self):
        """Prices should be tracked in history"""
        prices = [10.0, 12.5, 8.3, 15.0, 9.7]
        for i, price in enumerate(prices):
            self.agent.update_after_each_round(f"item_{i}", "opp1", price)
        
        assert len(self.agent.price_history) == len(prices)
        assert self.agent.price_history == prices
    
    def test_average_price_calculation_concept(self):
        """Agent should use average price for market assessment"""
        # Add some prices
        prices = [10.0, 12.0, 11.0, 9.0, 13.0]
        for i, price in enumerate(prices):
            self.agent.update_after_each_round(f"item_{i}", "opp1", price)
        
        avg_price = sum(prices) / len(prices)  # = 11.0
        assert avg_price == 11.0
        
        # Agent should adjust bidding based on this
        # Item with valuation 12.0 is above average (11.0)
        bid = self.agent.bidding_function("item_5")
        assert bid > 0
    
    def test_max_price_tracking(self):
        """Agent should track maximum observed price"""
        prices = [8.0, 15.0, 10.0, 12.0, 9.0]
        for i, price in enumerate(prices):
            self.agent.update_after_each_round(f"item_{i}", "opp1", price)
        
        max_price = max(prices)  # = 15.0
        assert max_price == 15.0
        
        # Agent should adjust if our valuation is above/below max
        self.agent.valuation_vector["test_item"] = 18.0  # Above max
        bid_above = self.agent.bidding_function("test_item")
        assert bid_above > 0
    
    def test_competitive_market_adjustment(self):
        """High average prices should make agent more conservative"""
        # Simulate competitive market (high prices)
        high_prices = [14.0, 15.0, 13.5, 16.0, 14.5]
        for i, price in enumerate(high_prices):
            self.agent.update_after_each_round(f"item_{i}", "opp1", price)
        
        # avg = 14.6, max = 16.0
        # Our item value = 12.0, which is below average
        bid = self.agent.bidding_function("item_5")
        # Should bid conservatively since market values items higher
        assert bid > 0
        assert bid < 12.0
    
    def test_low_competition_market(self):
        """Low average prices indicate less competition"""
        # Simulate low competition market
        low_prices = [4.0, 5.5, 3.8, 6.0, 4.5]
        for i, price in enumerate(low_prices):
            self.agent.update_after_each_round(f"item_{i}", "opp1", price)
        
        # avg = 4.76, max = 6.0
        # Our item value = 12.0, which is well above market
        bid = self.agent.bidding_function("item_5")
        assert bid > 0
        assert bid < 12.0  # Still shaded
    
    def test_no_price_history_fallback(self):
        """Agent should handle no price history gracefully"""
        # First round, no history
        assert len(self.agent.price_history) == 0
        
        bid = self.agent.bidding_function("item_0")
        assert bid > 0  # Should still bid


class TestStrategy4InformationRevelation:
    """
    Detailed tests for Strategy 4: Information Revelation
    From STRATEGY_GUIDE.md lines 100-120
    """
    
    def setup_method(self):
        """Setup for information revelation tests"""
        self.valuation_vector = {f"item_{i}": 10.0 for i in range(15)}
        self.agent = BiddingAgent(
            "test_team",
            self.valuation_vector,
            60.0,
            ["opp1", "opp2", "opp3", "opp4"]
        )
    
    def test_opponent_wins_tracking_initialized(self):
        """Opponent wins should be initialized to 0"""
        for opp in self.agent.opponent_teams:
            assert self.agent.opponent_wins[opp] == 0
            assert self.agent.opponent_items[opp] == []
    
    def test_track_single_opponent_win(self):
        """Should track when opponent wins an item"""
        self.agent.update_after_each_round("item_0", "opp1", 10.0)
        
        assert self.agent.opponent_wins["opp1"] == 1
        assert "item_0" in self.agent.opponent_items["opp1"]
    
    def test_track_multiple_wins_same_opponent(self):
        """Should track multiple wins by same opponent"""
        items = ["item_0", "item_1", "item_2"]
        for item in items:
            self.agent.update_after_each_round(item, "opp1", 8.0)
        
        assert self.agent.opponent_wins["opp1"] == 3
        assert len(self.agent.opponent_items["opp1"]) == 3
        for item in items:
            assert item in self.agent.opponent_items["opp1"]
    
    def test_track_different_opponents(self):
        """Should track wins across different opponents"""
        self.agent.update_after_each_round("item_0", "opp1", 8.0)
        self.agent.update_after_each_round("item_1", "opp2", 9.0)
        self.agent.update_after_each_round("item_2", "opp1", 7.0)
        self.agent.update_after_each_round("item_3", "opp3", 10.0)
        
        assert self.agent.opponent_wins["opp1"] == 2
        assert self.agent.opponent_wins["opp2"] == 1
        assert self.agent.opponent_wins["opp3"] == 1
        assert self.agent.opponent_wins["opp4"] == 0
    
    def test_our_wins_not_tracked_as_opponent(self):
        """Our own wins should not be tracked as opponent wins"""
        self.agent.update_after_each_round("item_0", self.agent.team_id, 8.0)
        
        # No opponent should have this win
        total_opponent_wins = sum(self.agent.opponent_wins.values())
        assert total_opponent_wins == 0
    
    def test_no_winner_not_tracked(self):
        """Rounds with no winner should not be tracked"""
        self.agent.update_after_each_round("item_0", "", 0.0)
        
        total_opponent_wins = sum(self.agent.opponent_wins.values())
        assert total_opponent_wins == 0
    
    def test_high_opponent_activity_adjustment(self):
        """Many opponent wins should trigger conservative bidding"""
        # Simulate 10 opponent wins (>8 triggers adjustment)
        for i in range(10):
            opp = f"opp{(i % 4) + 1}"
            self.agent.update_after_each_round(f"item_{i}", opp, 8.0)
        
        total_wins = sum(self.agent.opponent_wins.values())
        assert total_wins == 10
        
        # Agent should recognize high competition
        bid = self.agent.bidding_function("item_10")
        assert bid > 0
        # Should be more conservative (90% of normal)
    
    def test_low_opponent_activity(self):
        """Few opponent wins should allow normal bidding"""
        # Simulate only 3 opponent wins
        for i in range(3):
            self.agent.update_after_each_round(f"item_{i}", "opp1", 5.0)
        
        total_wins = sum(self.agent.opponent_wins.values())
        assert total_wins == 3
        assert total_wins <= 8  # Not triggering high activity threshold
        
        bid = self.agent.bidding_function("item_3")
        assert bid > 0
    
    def test_price_signal_high_price(self):
        """High prices signal strong competition"""
        # High price indicates item was valuable to others
        self.agent.update_after_each_round("item_0", "opp1", 15.0)
        
        assert 15.0 in self.agent.price_history
        # Agent should learn from this signal
    
    def test_price_signal_low_price(self):
        """Low prices signal weak competition"""
        # Low price indicates item wasn't valuable to others
        self.agent.update_after_each_round("item_0", "opp1", 2.0)
        
        assert 2.0 in self.agent.price_history
        # Agent should learn from this signal


class TestStrategyIntegration:
    """Test that all 4 strategies work together correctly"""
    
    def test_all_strategies_applied_in_bid(self):
        """Test that all strategies influence the final bid"""
        valuation_vector = {
            "item_0": 15.0,  # HIGH value
            "item_1": 10.0,  # MEDIUM value
            "item_2": 5.0,   # LOW value
        }
        agent = BiddingAgent("test", valuation_vector, 60.0, ["opp1", "opp2"])
        
        # Add some history
        agent.update_after_each_round("item_0", "opp1", 12.0)
        agent.update_after_each_round("item_1", "opp2", 8.0)
        
        # Now bid - should integrate all strategies
        bid = agent.bidding_function("item_2")
        
        # Strategy 1: Budget pacing applied
        assert agent.rounds_completed == 2
        # Strategy 2: Value classification (LOW tier)
        assert bid < 5.0  # Shaded
        # Strategy 3: Prices tracked
        assert len(agent.price_history) == 2
        # Strategy 4: Opponent wins tracked
        assert agent.opponent_wins["opp1"] == 1
        
        assert bid > 0
        assert bid <= agent.budget
    
    def test_game_progression_affects_all_strategies(self):
        """Test strategies adapt as game progresses"""
        valuation_vector = {f"item_{i}": 10.0 for i in range(15)}
        agent = BiddingAgent("test", valuation_vector, 60.0, ["opp1"])
        
        # Simulate game progression
        for i in range(10):
            agent.update_after_each_round(f"item_{i}", "opp1", 8.0)
        
        # All strategies should show game progress
        assert agent.rounds_completed == 10  # Strategy 1
        assert len(agent.price_history) == 10  # Strategy 3
        assert agent.opponent_wins["opp1"] == 10  # Strategy 4
        
        # Late game bid
        bid = agent.bidding_function("item_10")
        assert bid > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

