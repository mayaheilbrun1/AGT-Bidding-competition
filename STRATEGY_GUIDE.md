# AGT Competition - Strategy Guide

## 📋 Competition Requirements

### Auction Mechanics

- **Auction Type**: Second-price sealed-bid (Vickrey auction)
- **Budget**: 60 units per game (does NOT carry over between games)
- **Rounds**: 15 rounds per game
- **Timeout**: 3 seconds per bid decision
- **Information**: After each round, you learn winner + price paid (NOT all bids)

### Item Valuation Distribution

Each game, valuations are generated as follows:

- **6 items**: High-value for ALL teams (each team gets value U[10, 20])
- **4 items**: Low-value for ALL teams (each team gets value U[1, 10])
- **10 items**: Mixed values (each team gets value U[1, 20])

**Important**: You don't know which category each item belongs to! A high-value item in your valuation might be high-value for everyone (competitive) or only for you (less competitive).

### Strategic Challenge

In a standard second-price auction (without budget constraints):

- **Optimal Strategy**: Bid your true valuation
- **Why**: You win if your value > others, pay less than your value
- **With Budget Constraints**: This changes! You need to be more strategic

---

## 💡 Key Strategic Considerations

### 1. Budget Pacing

```python
# Calculate how much budget per remaining round
total_rounds = 15  # Always 15 rounds per game
rounds_remaining = total_rounds - self.rounds_completed
budget_per_round = self.budget / rounds_remaining if rounds_remaining > 0 else 0

# Be more aggressive as game progresses
progress = self.rounds_completed / total_rounds
aggressiveness = 0.7 + (0.3 * progress)  # 70% to 100%
```

**Key Questions:**

- How much to spend now vs. save for later?
- Should you reserve budget for high-value items that might come later?
- How to avoid running out of budget before the game ends?

### 2. Value Classification

```python
# Classify items based on your valuation
high_value_threshold = 12.0
low_value_threshold = 8.0

if my_valuation > high_value_threshold:
    # Might be competitive, bid carefully
    bid = my_valuation * 0.9
elif my_valuation < low_value_threshold:
    # Low value, bid conservatively
    bid = my_valuation * 0.5
else:
    # Medium value
    bid = my_valuation * 0.7
```

**Key Questions:**

- Which items are worth competing for aggressively?
- Should you give up on highly competitive items to save budget?
- How to identify items where you might have a valuation advantage?

### 3. Opponent Modeling

```python
# Track observed prices
self.observed_prices.append(price_paid)

# Estimate market competitiveness
avg_price = sum(self.observed_prices) / len(self.observed_prices)
max_price = max(self.observed_prices)

# Adjust strategy based on market
if avg_price > 10:  # Competitive market
    # Be more conservative on medium-value items
    pass
```

**Key Questions:**

- Can you learn from observed prices to predict competition?
- Are certain opponents more aggressive than others?
- How can you exploit opponent patterns?

### 4. Information Revelation

What you can learn from each round:

- **Price paid**: Indicates second-highest bid (at least)
- **Winner identity**: Track which teams are winning
- **No winner**: Everyone bid low (item not valuable to others)

```python
# Track opponent success
if winning_team != self.team_id and winning_team:
    self.opponent_wins[winning_team] = \
        self.opponent_wins.get(winning_team, 0) + 1
```

**Key Insights:**

- If price paid is low, the item might not be valuable to others
- If price paid is high, there's strong competition
- Track which opponents are winning to identify aggressive bidders
- When there's no winner, the item was undervalued by everyone

---

## 🚀 Advanced Strategies

### 1. Bayesian Belief Updates

```python
# Maintain beliefs about opponent valuations
# Update after observing their bids (revealed when they win)
# Use to predict future competition
```

**Concept**: After observing which items opponents win and at what price, update your beliefs about:

- Their valuation distributions
- Their budget constraints
- Their bidding strategies

**Implementation Ideas:**

- Track which items each opponent wins
- Infer their valuations from the prices they pay (remember: they pay second-highest bid)
- Predict which future items they'll compete for

### 2. Shading Strategy

```python
# In second-price auctions with budgets, you might want to "shade" bids
# Bid less than true value to preserve budget
shading_factor = 0.8  # Bid 80% of valuation
bid = my_valuation * shading_factor
```

**Concept**: Bidding below your true valuation to:

- Preserve budget for future rounds
- Avoid overpaying in competitive auctions
- Balance winning probability vs. budget conservation

**Trade-offs:**

- **More shading**: Save more budget, but win fewer items
- **Less shading**: Win more items, but might exhaust budget early

### 3. End-Game Strategy

```python
# Near end of game, spend remaining budget more aggressively
if rounds_remaining <= 3:
    # Less need to preserve budget
    bid = min(my_valuation, self.budget * 0.8)
```

**Concept**: As the game nears its end, the value of preserving budget decreases.

**Considerations:**

- In final rounds, you should be willing to spend remaining budget
- Unused budget at game end provides zero value
- Balance between spending aggressively vs. not overpaying
- Consider that opponents may also bid more aggressively at the end

### 4. Adaptive Competitiveness

**Concept**: Adjust your bidding aggressiveness based on observed market conditions.

```python
# Example: Adjust strategy based on market observations
if len(self.price_history) >= 5:
    recent_avg = sum(self.price_history[-5:]) / 5
    overall_avg = sum(self.price_history) / len(self.price_history)

    if recent_avg > overall_avg * 1.2:
        # Market heating up - be more conservative
        shading_factor = 0.7
    elif recent_avg < overall_avg * 0.8:
        # Market cooling down - can be more aggressive
        shading_factor = 0.9
    else:
        # Stable market
        shading_factor = 0.8
```

### 5. Risk Management

**Concept**: Balance risk vs. reward based on game state.

**Early Game** (Rounds 1-5):

- Be conservative to gather information
- Don't commit too much budget
- Learn opponent patterns

**Mid Game** (Rounds 6-10):

- Adjust strategy based on observations
- Compete for high-value items
- Maintain budget discipline

**Late Game** (Rounds 11-15):

- Increase aggressiveness
- Spend remaining budget strategically
- Focus on positive-utility items

### 6. Probabilistic Item Classification

**Concept**: Inferring item categories from observed bidding patterns and market signals.

Since you don't know which items belong to which distribution category (high-value for all, low-value for all, or mixed), you can use Bayesian inference to estimate probabilities based on observed outcomes.

**Key Insight**: If an item has high value for you AND the winning price is high, it's more likely to be from the "high-value for all teams" category (6 such items exist). Conversely, if you value it highly but the price is low, it might be a mixed-value item where you have an advantage.

**Implementation Ideas:**

```python
def estimate_item_category_probability(self, item_id: str, price_paid: float):
    """
    Estimate probability that an item belongs to each category based on
    observed price and your own valuation.

    Categories:
    - HIGH_FOR_ALL: 6 items with valuations U[10, 20] for everyone
    - LOW_FOR_ALL: 4 items with valuations U[1, 10] for everyone
    - MIXED: 10 items with valuations U[1, 20] for everyone
    """
    my_valuation = self.valuation_vector[item_id]

    # Prior probabilities based on distribution
    prior_high = 6/20  # 30% chance item is high-value for all
    prior_low = 4/20   # 20% chance item is low-value for all
    prior_mixed = 10/20  # 50% chance item is mixed

    # Likelihood: P(high_price | category)
    # If price is high AND my value is high → likely HIGH_FOR_ALL
    # If price is low AND my value is high → likely MIXED (I have advantage)
    # If price is low AND my value is low → likely LOW_FOR_ALL

    if my_valuation > 12 and price_paid > 10:
        # Strong signal for HIGH_FOR_ALL category
        prob_high_for_all = 0.7
        prob_mixed = 0.25
        prob_low_for_all = 0.05
    elif my_valuation > 12 and price_paid < 6:
        # High value for me, low competition → likely MIXED
        prob_high_for_all = 0.1
        prob_mixed = 0.85
        prob_low_for_all = 0.05
    elif my_valuation < 8 and price_paid < 6:
        # Low value for me, low competition → likely LOW_FOR_ALL
        prob_high_for_all = 0.05
        prob_mixed = 0.25
        prob_low_for_all = 0.7
    else:
        # Unclear signal, use priors
        prob_high_for_all = prior_high
        prob_low_for_all = prior_low
        prob_mixed = prior_mixed

    return {
        'high_for_all': prob_high_for_all,
        'low_for_all': prob_low_for_all,
        'mixed': prob_mixed
    }
```

**Strategic Applications:**

1. **Competitive Assessment**: Items likely in HIGH_FOR_ALL category require more aggressive bidding or strategic withdrawal to save budget.

2. **Opportunity Identification**: Items in MIXED category where you have high valuation but low competition are golden opportunities.

3. **Budget Allocation**: Knowing the remaining distribution helps you allocate budget more efficiently.

```python
# Track category estimates across all observed items
def update_beliefs_after_round(self, item_id: str, winning_team: str, price_paid: float):
    """Update beliefs about item categories"""
    category_probs = self.estimate_item_category_probability(item_id, price_paid)
    self.item_category_beliefs[item_id] = category_probs

    # Use this to predict future item competitiveness
    # Example: If we've seen 3 HIGH_FOR_ALL items, only 3 remain
```

### 7. Opponent Budget Tracking

**Concept**: Monitor opponent spending patterns to infer their remaining budgets and predict future behavior.

**Key Insight**: If a team has won many items at high prices, they likely have less budget remaining and will be less competitive in future rounds. This creates opportunities for you.

**Implementation Ideas:**

```python
class OpponentTracker:
    def __init__(self, opponent_teams: List[str]):
        self.opponent_budgets = {opp: 60.0 for opp in opponent_teams}
        self.opponent_items_won = {opp: [] for opp in opponent_teams}
        self.opponent_total_spent = {opp: 0.0 for opp in opponent_teams}

    def update_after_auction(self, winning_team: str, price_paid: float, item_id: str):
        """Track opponent spending and estimate remaining budgets"""
        if winning_team and winning_team != self.team_id:
            # Update estimates
            self.opponent_budgets[winning_team] -= price_paid
            self.opponent_total_spent[winning_team] += price_paid
            self.opponent_items_won[winning_team].append(item_id)

    def estimate_opponent_aggressiveness(self, opponent_team: str) -> float:
        """
        Estimate how aggressively an opponent will bid based on their
        remaining budget and items won.

        Returns: float between 0 (passive) and 1 (aggressive)
        """
        remaining_budget = self.opponent_budgets.get(opponent_team, 60.0)
        items_won = len(self.opponent_items_won.get(opponent_team, []))
        total_spent = self.opponent_total_spent.get(opponent_team, 0.0)

        # If they have low budget, they'll be less competitive
        budget_factor = remaining_budget / 60.0

        # If they've won many items, they might be more conservative now
        items_factor = max(0, 1 - (items_won / 10))

        # Combine factors
        aggressiveness = (budget_factor * 0.6) + (items_factor * 0.4)

        return aggressiveness

    def identify_weak_opponents(self, threshold: float = 20.0) -> List[str]:
        """Find opponents with low remaining budget"""
        return [opp for opp, budget in self.opponent_budgets.items()
                if budget < threshold]
```

**Strategic Applications:**

```python
def bidding_function(self, item_id: str) -> float:
    my_valuation = self.valuation_vector[item_id]

    # Check if most opponents are budget-constrained
    weak_opponents = self.tracker.identify_weak_opponents(threshold=15.0)

    if len(weak_opponents) >= 3:
        # Less competition expected - bid more conservatively
        bid = my_valuation * 0.6
    else:
        # Still strong competition - bid normally
        bid = my_valuation * 0.8

    return bid
```

### 8. Structured Decision Tree

**Concept**: Use a systematic decision-making framework to quickly evaluate bidding options under time constraints.

**Key Insight**: Since you only have 3 seconds per decision, you need a fast, analytical decision tree that considers: (1) item value, (2) budget constraints, (3) game state, and (4) expected competition.

**Decision Tree Structure:**

```python
def structured_bidding_decision(self, item_id: str) -> float:
    """
    Systematic decision tree for bid calculation
    Time-optimized to complete in < 3 seconds
    """
    my_valuation = self.valuation_vector[item_id]
    rounds_remaining = self.total_rounds - self.rounds_completed

    # DECISION NODE 1: Do I want this item? (Utility potential)
    if my_valuation < 3.0:
        return 0.0  # Not worth bidding - save computation time

    # DECISION NODE 2: Can I afford to bid meaningfully?
    if self.budget < 1.0:
        return 0.0  # Insufficient budget

    # DECISION NODE 3: What's my budget allocation for this round?
    budget_per_round = self.budget / max(1, rounds_remaining)
    max_affordable_bid = min(my_valuation, budget_per_round * 2.5)

    # DECISION NODE 4: What's the expected competition level?
    expected_competition = self.estimate_competition_level(item_id)

    # DECISION NODE 5: Calculate base bid using value and competition
    if expected_competition == "HIGH":
        # High competition: bid conservatively or fold
        if my_valuation > 15:
            bid = my_valuation * 0.75  # Still valuable, bid lower
        else:
            return 0.0  # Not worth competing

    elif expected_competition == "MEDIUM":
        # Medium competition: standard shading
        bid = my_valuation * 0.80

    else:  # LOW competition
        # Low competition: bid conservatively to win cheaply
        bid = my_valuation * 0.60

    # DECISION NODE 6: Apply game phase adjustments
    game_progress = self.rounds_completed / self.total_rounds

    if game_progress > 0.8:  # End game (rounds 13-15)
        bid = min(bid * 1.2, self.budget * 0.9)  # More aggressive
    elif game_progress < 0.3:  # Early game (rounds 1-4)
        bid = bid * 0.85  # More conservative

    # DECISION NODE 7: Final constraints
    final_bid = max(0.0, min(bid, max_affordable_bid, self.budget))

    return round(final_bid, 2)


def estimate_competition_level(self, item_id: str) -> str:
    """
    Quick estimation of competition level
    Returns: "HIGH", "MEDIUM", or "LOW"
    """
    my_valuation = self.valuation_vector[item_id]

    # Use historical price data
    if self.price_history:
        avg_price = sum(self.price_history) / len(self.price_history)
        max_price = max(self.price_history)

        # If my valuation is high and market has shown high prices
        if my_valuation > 12 and avg_price > 8:
            return "HIGH"
        elif my_valuation > 8 and avg_price > 5:
            return "MEDIUM"
        else:
            return "LOW"
    else:
        # No data yet - use valuation as proxy
        if my_valuation > 14:
            return "HIGH"  # Likely competitive
        elif my_valuation > 8:
            return "MEDIUM"
        else:
            return "LOW"
```

**Performance Optimization:**

```python
# Pre-compute expensive calculations in __init__ or update_after_each_round
def __init__(self, team_id, valuation_vector, budget, opponent_teams):
    # ... standard initialization ...

    # Pre-sort items by value for quick reference
    self.items_by_value = sorted(
        valuation_vector.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Pre-classify items into value tiers
    self.high_value_items = [item for item, val in valuation_vector.items() if val > 14]
    self.medium_value_items = [item for item, val in valuation_vector.items() if 8 <= val <= 14]
    self.low_value_items = [item for item, val in valuation_vector.items() if val < 8]
```

**Decision Tree Visualization:**

```
START: Item announced
  |
  ├─> Item value < 3? → BID 0
  |
  ├─> Budget < 1? → BID 0
  |
  ├─> Estimate competition level
  |     ├─> HIGH + Value < 15? → BID 0
  |     ├─> HIGH + Value >= 15? → BID Value * 0.75
  |     ├─> MEDIUM? → BID Value * 0.80
  |     └─> LOW? → BID Value * 0.60
  |
  ├─> Adjust for game phase
  |     ├─> End game (80%+)? → Multiply by 1.2
  |     ├─> Early game (<30%)? → Multiply by 0.85
  |     └─> Mid game? → No change
  |
  └─> Apply budget constraints → RETURN final bid
```

This structured approach ensures:

- **Fast execution** (< 3 seconds)
- **Consistent logic** across all decisions
- **Easy debugging** and refinement
- **Analytical reasoning** rather than ad-hoc decisions

### 9. Explore-Exploit Trade-off (Multi-Armed Bandit)

**Concept**: Balance between gathering information about opponents (exploration) and maximizing immediate utility (exploitation).

**Key Insight**: Early rounds are valuable for learning opponent behavior, but you also need to win items. The optimal strategy shifts from exploration to exploitation as the game progresses. **Crucially: Only explore on low-to-medium value items** - never waste high-value items on experimentation.

**Implementation Ideas:**

```python
class ExploreExploitStrategy:
    def __init__(self, valuation_vector: Dict[str, float]):
        self.exploration_rate = 0.3  # 30% exploration in early game
        self.min_exploration_rate = 0.05  # 5% exploration in late game

        # Calculate value thresholds based on your valuations
        all_values = list(valuation_vector.values())
        self.high_value_threshold = np.percentile(all_values, 70)  # Top 30%
        self.low_value_threshold = np.percentile(all_values, 30)   # Bottom 30%

    def get_exploration_factor(self, rounds_completed: int, total_rounds: int = 15) -> float:
        """
        Decay exploration rate as game progresses
        Early game: explore more (bid at different levels to learn)
        Late game: exploit learned information
        """
        progress = rounds_completed / total_rounds
        exploration = self.exploration_rate * (1 - progress) + self.min_exploration_rate
        return exploration

    def should_explore(self, rounds_completed: int, item_value: float) -> bool:
        """
        Decide whether to make an exploratory bid
        Consider both game progress AND item value

        Args:
            rounds_completed: Number of rounds finished
            item_value: How valuable this item is to you

        Returns:
            bool: True if should explore on this item
        """
        import random

        # NEVER explore on high-value items
        if item_value > self.high_value_threshold:
            return False

        # Base exploration rate from game progress
        base_exploration = self.get_exploration_factor(rounds_completed)

        # Adjust exploration probability by item value
        # Low value items: explore more freely
        # Medium value items: explore cautiously
        if item_value < self.low_value_threshold:
            # Low value item - safe to explore
            exploration_probability = base_exploration * 1.5  # Boost exploration
        elif item_value < self.high_value_threshold:
            # Medium value item - careful exploration
            exploration_probability = base_exploration * 0.7  # Reduce exploration
        else:
            # High value - already returned False above
            exploration_probability = 0.0

        # Cap at reasonable maximum
        exploration_probability = min(exploration_probability, 0.4)

        return random.random() < exploration_probability

    def exploratory_bid(self, my_valuation: float, item_value: float) -> float:
        """
        Make an exploratory bid to learn opponent responses
        Vary bid level to test different price points

        For low-value items: test wider range (aggressive exploration)
        For medium-value items: test narrower range (conservative exploration)
        """
        import random

        if item_value < self.low_value_threshold:
            # Low value - test wide range
            # Sometimes bid very low to see if others compete
            # Sometimes bid higher to see who responds
            variation = random.choice([
                random.uniform(0.3, 0.6),  # Very conservative
                random.uniform(0.7, 0.9),  # Moderate
                random.uniform(0.9, 1.2),  # Aggressive
            ])
        else:
            # Medium value - narrower range
            variation = random.uniform(0.7, 1.0)

        return my_valuation * variation
```

**Strategic Applications:**

```python
def bidding_function(self, item_id: str) -> float:
    my_valuation = self.valuation_vector[item_id]

    # Decide if this is an exploration opportunity
    should_explore = self.explore_exploit.should_explore(
        self.rounds_completed,
        my_valuation  # Item value is now a factor!
    )

    if should_explore:
        # Make exploratory bid on low/medium value items
        bid = self.explore_exploit.exploratory_bid(my_valuation, my_valuation)
        print(f"[EXPLORE] Testing bid {bid:.2f} for item {item_id} (value={my_valuation:.2f})")
        return min(bid, self.budget)

    # Otherwise: exploit learned information (normal bidding)
    bid = self.calculate_optimal_bid(item_id)
    return bid
```

**Value-Based Exploration Strategy:**

```python
class ValueAwareExploration:
    """
    Sophisticated exploration that maximizes information gain
    while minimizing opportunity cost
    """

    def calculate_exploration_value(self, item_value: float,
                                   rounds_completed: int,
                                   information_gap: float) -> float:
        """
        Calculate the value of exploring on this item

        Returns: exploration_value (higher = more worth exploring)
        """
        # Information gain potential (how much we can learn)
        information_value = information_gap * 5.0

        # Opportunity cost (what we lose by not bidding optimally)
        opportunity_cost = item_value * 0.3  # Assume 30% potential loss

        # Time value (exploration worth more early)
        rounds_remaining = 15 - rounds_completed
        time_value = rounds_remaining / 15.0

        # Net exploration value
        exploration_value = (information_value * time_value) - opportunity_cost

        return exploration_value

    def should_explore_intelligent(self, item_value: float,
                                   rounds_completed: int,
                                   opponent_knowledge: float) -> bool:
        """
        Intelligent exploration decision

        Args:
            item_value: Value of current item
            rounds_completed: Game progress
            opponent_knowledge: How much we know about opponents (0-1)
                              0 = know nothing, 1 = perfect knowledge
        """
        # Don't explore if we already know enough
        if opponent_knowledge > 0.7:
            return False

        # Don't explore on high value items
        if item_value > 14:
            return False

        # Don't explore late in game
        if rounds_completed > 10:
            return False

        # Calculate information gap (how much we still need to learn)
        information_gap = 1.0 - opponent_knowledge

        # Calculate exploration value
        exploration_value = self.calculate_exploration_value(
            item_value, rounds_completed, information_gap
        )

        # Explore if value is positive and significant
        return exploration_value > 2.0
```

**Example Usage in Full Context:**

```python
def __init__(self, team_id, valuation_vector, budget, opponent_teams):
    # ... standard initialization ...

    self.explore_exploit = ExploreExploitStrategy(valuation_vector)
    self.opponent_knowledge = 0.0  # Track how much we've learned
    self.rounds_completed = 0

def update_after_each_round(self, item_id, winning_team, price_paid):
    # ... standard updates ...

    # Update knowledge level based on new information
    if price_paid > 0:
        # We learned something about opponent behavior
        self.opponent_knowledge = min(1.0, self.opponent_knowledge + 0.1)

    self.rounds_completed += 1

def bidding_function(self, item_id: str) -> float:
    my_valuation = self.valuation_vector[item_id]

    # Value-aware exploration decision
    if (self.rounds_completed < 8 and  # Only in first half
        my_valuation < 12 and           # Only on non-premium items
        self.opponent_knowledge < 0.6): # Only if we need more info

        should_explore = self.explore_exploit.should_explore(
            self.rounds_completed,
            my_valuation
        )

        if should_explore:
            bid = self.explore_exploit.exploratory_bid(my_valuation, my_valuation)
            return min(bid, self.budget)

    # Normal exploitation bidding
    bid = self.calculate_optimal_bid(item_id)
    return bid
```

**Key Principles:**

1. **Never explore on high-value items** (>70th percentile of your valuations)
2. **Prefer exploring on low-value items** where opportunity cost is minimal
3. **Stop exploring once you have sufficient information** about opponents
4. **Stop exploring after round 10** - focus on winning
5. **Exploration intensity** should be inversely proportional to item value



---

## 🔬 Optional Advanced Strategies (Implement If Time Permits)

The following strategies are more complex and time-intensive to implement. **Start with strategies 1-10 first**, then add these if you have time and want to further optimize your agent.
### 10. Regret Minimization

**Concept**: Minimize expected regret - the difference between your actual utility and the utility you could have achieved with perfect information.

**Key Insight**: You won't win every item, but you want to minimize regret about the items you didn't pursue aggressively enough or the ones you overpaid for.

**Implementation Ideas:**

```python
class RegretMinimizer:
    def __init__(self):
        self.missed_opportunities = []  # Items we should have bid higher on
        self.overpayments = []  # Items we paid too much for

    def calculate_regret(self, item_id: str, my_bid: float,
                        winning_bid: float, my_valuation: float):
        """
        Calculate regret after each auction
        """
        if winning_bid > 0 and my_bid < winning_bid:
            # We lost - calculate opportunity cost
            if my_bid < my_valuation:
                potential_utility = my_valuation - winning_bid
                if potential_utility > 0:
                    # We could have won with positive utility
                    regret = potential_utility
                    self.missed_opportunities.append({
                        'item': item_id,
                        'regret': regret,
                        'should_have_bid': winning_bid + 0.01
                    })

    def learn_from_regret(self) -> float:
        """
        Adjust future bidding based on past regrets
        Returns: aggression_factor (>1.0 means bid higher)
        """
        if len(self.missed_opportunities) > 3:
            # We're missing too many opportunities - bid more aggressively
            avg_regret = sum(r['regret'] for r in self.missed_opportunities[-5:]) / 5
            if avg_regret > 3.0:
                return 1.15  # Bid 15% higher
            elif avg_regret > 1.5:
                return 1.08  # Bid 8% higher

        return 1.0  # No adjustment
```

### 11. Statistical Opponent Modeling ⏰ (Complex - High Implementation Time)

**Concept**: Build statistical models of opponent bidding behavior to predict future bids.

**Key Insight**: Opponents reveal information through their winning bids. Use regression or probability distributions to model their behavior.

**Complexity**: High - requires statistical modeling, data tracking, and prediction algorithms.

**Implementation Ideas:**

```python
import numpy as np
from typing import Dict, List, Tuple

class OpponentStatisticalModel:
    def __init__(self, opponent_teams: List[str]):
        # Track (item_value_estimate, winning_bid) pairs for each opponent
        self.opponent_data = {opp: [] for opp in opponent_teams}
        self.opponent_bid_ratios = {opp: [] for opp in opponent_teams}

    def update_model(self, winning_team: str, price_paid: float,
                    estimated_winner_valuation: float):
        """
        When an opponent wins, estimate their valuation and track bid ratio
        In second-price auction: winner's bid >= price_paid
        Winner's valuation is likely >= price_paid (otherwise irrational)
        """
        if winning_team in self.opponent_data:
            # Estimate their valuation (lower bound is price they paid)
            estimated_valuation = max(price_paid, estimated_winner_valuation)
            self.opponent_data[winning_team].append({
                'price': price_paid,
                'estimated_value': estimated_valuation
            })

            # Track what fraction of value they bid
            if estimated_valuation > 0:
                bid_ratio = price_paid / estimated_valuation
                self.opponent_bid_ratios[winning_team].append(bid_ratio)

    def predict_opponent_bid(self, opponent_team: str,
                            item_valuation_estimate: float) -> float:
        """
        Predict what an opponent will bid based on their history
        """
        if opponent_team not in self.opponent_bid_ratios:
            return item_valuation_estimate * 0.8  # Default assumption

        ratios = self.opponent_bid_ratios[opponent_team]
        if len(ratios) < 2:
            return item_valuation_estimate * 0.8

        # Use median bid ratio (more robust than mean)
        median_ratio = np.median(ratios)
        predicted_bid = item_valuation_estimate * median_ratio

        return predicted_bid

    def estimate_winning_probability(self, my_bid: float,
                                     item_valuation_estimate: float) -> float:
        """
        Estimate probability of winning given your bid
        """
        # Predict what each opponent might bid
        predicted_opponent_bids = []
        for opp in self.opponent_data.keys():
            pred_bid = self.predict_opponent_bid(opp, item_valuation_estimate)
            predicted_opponent_bids.append(pred_bid)

        if not predicted_opponent_bids:
            return 0.5  # No information

        # Probability = fraction of opponents you'll beat
        beats = sum(1 for opp_bid in predicted_opponent_bids if my_bid > opp_bid)
        return beats / len(predicted_opponent_bids)
```

**Performance Note**: This adds computation time. Ensure bidding_function still completes in < 3 seconds.

### 12. Expected Utility Maximization ⏰ (Moderate - Depends on Strategy 11)

**Concept**: For each bidding decision, calculate expected utility considering win probability and potential payoff.

**Key Insight**: Don't just bid based on value - bid based on expected utility = P(win) × (value - expected_price)

**Complexity**: Moderate - requires iterating through bid options and probability estimation.

**Dependencies**: Works best with Statistical Opponent Modeling (Strategy 11).

**Implementation Ideas:**

```python
def calculate_expected_utility_bid(self, item_id: str) -> float:
    """
    Choose bid that maximizes expected utility
    EU(bid) = P(win | bid) × (valuation - expected_price_if_win)
    """
    my_valuation = self.valuation_vector[item_id]

    # Test different bid levels
    best_bid = 0
    best_expected_utility = 0

    # Try bids from 50% to 100% of valuation
    for bid_fraction in np.arange(0.5, 1.05, 0.05):
        test_bid = my_valuation * bid_fraction

        if test_bid > self.budget:
            break

        # Estimate probability of winning with this bid
        win_prob = self.opponent_model.estimate_winning_probability(
            test_bid, my_valuation
        )

        # Expected price = average of second-highest bids
        # Approximate: if you bid X and win, you probably pay 0.8*X
        expected_price = test_bid * 0.85  # Conservative estimate

        # Expected utility = P(win) × (value - price)
        expected_utility = win_prob * (my_valuation - expected_price)

        if expected_utility > best_expected_utility:
            best_expected_utility = expected_utility
            best_bid = test_bid

    return best_bid
```

**Performance Consideration**: This requires a loop. Test to ensure < 3 second completion time.

### 13. Portfolio Diversification Strategy ⏰ (Low-Moderate)

**Concept**: Treat your budget allocation like a portfolio - diversify across items to reduce risk.

**Key Insight**: Don't put all your budget into competing for a few high-value items. Spread risk by winning multiple medium-value items.

**Complexity**: Low-Moderate - straightforward classification and allocation logic.

**Implementation Ideas:**

```python
class PortfolioStrategy:
    def __init__(self, valuation_vector: Dict[str, float]):
        self.target_items = 5  # Aim to win ~5 items per game
        self.risk_tolerance = 0.3  # 30% of budget for risky bids

    def classify_items_by_risk(self, valuation_vector: Dict[str, float],
                               price_history: List[float]) -> Dict[str, List[str]]:
        """
        Classify items as safe vs risky investments
        """
        avg_market_price = np.mean(price_history) if price_history else 8.0

        safe_items = []  # Low competition expected
        risky_items = []  # High competition expected

        for item_id, value in valuation_vector.items():
            if value > 12 and avg_market_price > 8:
                risky_items.append(item_id)  # High value + competitive market
            else:
                safe_items.append(item_id)

        return {'safe': safe_items, 'risky': risky_items}

    def allocate_budget(self, current_budget: float, rounds_remaining: int) -> Dict:
        """
        Allocate budget between safe and risky bids
        """
        # Reserve more budget for safe bids to ensure wins
        safe_budget = current_budget * (1 - self.risk_tolerance)
        risky_budget = current_budget * self.risk_tolerance

        # Adjust based on game progress
        if rounds_remaining <= 5:
            # Late game: take more risks
            safe_budget = current_budget * 0.6
            risky_budget = current_budget * 0.4

        return {
            'safe_budget': safe_budget,
            'risky_budget': risky_budget,
            'safe_per_round': safe_budget / max(1, rounds_remaining),
            'risky_per_round': risky_budget / max(1, rounds_remaining)
        }
```

### 14. Dynamic Programming for Budget Allocation ⏰ (High - Advanced)

**Concept**: Use dynamic programming to find optimal budget allocation across remaining rounds.

**Key Insight**: This is similar to the "knapsack problem" - you have limited budget and need to choose which items to pursue for maximum value.

**Complexity**: High - requires DP algorithm, may be challenging to implement and debug.

**Implementation Ideas:**

```python
def optimize_remaining_strategy(self, remaining_items: List[str],
                               current_budget: float) -> Dict[str, float]:
    """
    Calculate optimal bid allocation for remaining unseen items
    Assumes you have estimates of item values
    """
    # This is a simplified version - full DP is complex

    # Sort remaining items by value/expected_cost ratio
    item_scores = []
    for item_id in remaining_items:
        estimated_value = self.valuation_vector.get(item_id, 10)
        estimated_cost = self.estimate_item_cost(item_id)

        if estimated_cost > 0:
            efficiency = estimated_value / estimated_cost
            item_scores.append((item_id, efficiency, estimated_value, estimated_cost))

    # Sort by efficiency (value per unit cost)
    item_scores.sort(key=lambda x: x[1], reverse=True)

    # Greedy allocation (approximation of DP solution)
    allocation = {}
    remaining_budget = current_budget

    for item_id, efficiency, value, cost in item_scores:
        # Allocate budget to high-efficiency items
        if remaining_budget >= cost:
            allocation[item_id] = min(cost * 1.1, remaining_budget * 0.3)
            remaining_budget -= allocation[item_id]
        else:
            allocation[item_id] = remaining_budget * 0.5
            break

    return allocation
```

**Note**: Full DP solution is complex. This shows a simplified greedy approximation.

### 15. Counter-Strategy Matrix ⏰ (Moderate)

**Concept**: Identify opponent strategy types and use appropriate counter-strategies.

**Key Insight**: Different opponents use different strategies (aggressive, conservative, truthful). Detect their type and counter appropriately.

**Implementation Ideas:**

```python
class StrategyClassifier:
    """Classify and counter different opponent strategies"""

    def classify_opponent_strategy(self, opponent_team: str,
                                   observations: List[Dict]) -> str:
        """
        Classify opponent as: AGGRESSIVE, CONSERVATIVE, TRUTHFUL, or ADAPTIVE
        """
        if len(observations) < 3:
            return "UNKNOWN"

        # Analyze patterns
        high_bids = sum(1 for obs in observations if obs['price'] > 12)
        low_bids = sum(1 for obs in observations if obs['price'] < 6)
        total = len(observations)

        if high_bids / total > 0.6:
            return "AGGRESSIVE"
        elif low_bids / total > 0.6:
            return "CONSERVATIVE"
        elif self.check_truthful_pattern(observations):
            return "TRUTHFUL"
        else:
            return "ADAPTIVE"

    def get_counter_strategy(self, opponent_type: str) -> Dict:
        """
        Return counter-strategy parameters
        """
        counter_strategies = {
            "AGGRESSIVE": {
                "description": "Avoid direct competition, bid on items they ignore",
                "shading_factor": 0.6,
                "competition_avoidance": 0.8
            },
            "CONSERVATIVE": {
                "description": "Bid slightly above them to win at low prices",
                "shading_factor": 0.75,
                "competition_avoidance": 0.3
            },
            "TRUTHFUL": {
                "description": "Shade bids more since they bid full value",
                "shading_factor": 0.7,
                "competition_avoidance": 0.5
            },
            "ADAPTIVE": {
                "description": "Use mixed strategy to stay unpredictable",
                "shading_factor": 0.75,
                "competition_avoidance": 0.5
            }
        }

        return counter_strategies.get(opponent_type, counter_strategies["ADAPTIVE"])
```

---

## 🎯 Strategy Development Checklist

When developing your strategy, consider:

- [ ] **Budget Management**: Do you have a pacing strategy?
- [ ] **Value Assessment**: How do you decide which items to compete for?
- [ ] **Opponent Learning**: Are you tracking and learning from opponent behavior?
- [ ] **Adaptive Bidding**: Does your strategy adjust based on observations?
- [ ] **End-Game Planning**: Do you spend remaining budget effectively?
- [ ] **Risk Management**: Do you balance aggressive vs. conservative bidding?
- [ ] **Edge Cases**: Does your strategy handle zero budget, final round, etc.?
- [ ] **Performance**: Does your bidding function complete in < 3 seconds?

---

## 📊 Evaluation Criteria

Your strategy will be evaluated on:

1. **Total Utility**: Sum of (values won - prices paid) across all games
2. **Consistency**: Stable performance across different opponents and conditions
3. **Budget Efficiency**: Effective use of available budget
4. **Adaptability**: Ability to adjust to different market conditions
5. **Robustness**: Handling edge cases and unexpected scenarios

---

## 🎓 Final Tips

1. **Start Simple**: Begin with basic strategy, then incrementally add sophistication
2. **Test Extensively**: Run simulations with different opponents and random seeds
3. **Analyze Failures**: When you lose, understand why and adjust
4. **Balance Exploration vs. Exploitation**: Learn early, exploit later
5. **Remember Second-Price Properties**: You pay second-highest bid, not your own
6. **Think Sequential**: Each round affects future rounds through budget and information
7. **Model Uncertainty**: You don't know which items will be auctioned or their order
8. **Consider Opponent Rationality**: What would a smart opponent do?

Good luck! 🏆
