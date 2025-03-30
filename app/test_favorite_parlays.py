"""
Test script for favorite parlay generation

This script tests the parlay generation algorithm with different sample datasets
to help diagnose why favorite parlays are not being generated properly.
"""

from parlay_recommendations import ParlayRecommender
import random
import json

def generate_test_bets(count=20, min_odds=1.2, max_odds=3.0):
    """Generate test bets with various odds in the typical range for favorites"""
    test_bets = []
    
    sports = ["NBA", "NFL", "MLB", "NHL", "MMA"]
    teams_by_sport = {
        "NBA": ["Lakers", "Celtics", "Bulls", "Warriors", "Heat", "Bucks", "Nets", "Suns"],
        "NFL": ["Chiefs", "Eagles", "Cowboys", "49ers", "Bills", "Ravens", "Lions", "Packers"],
        "MLB": ["Yankees", "Dodgers", "Red Sox", "Cubs", "Astros", "Braves", "Cardinals", "Mets"],
        "NHL": ["Maple Leafs", "Bruins", "Canadiens", "Blackhawks", "Penguins", "Lightning", "Oilers", "Rangers"],
        "MMA": ["Fighter1", "Fighter2", "Fighter3", "Fighter4", "Fighter5", "Fighter6", "Fighter7", "Fighter8"]
    }
    
    for i in range(count):
        sport = random.choice(sports)
        team = random.choice(teams_by_sport[sport])
        
        # Generate odds that are realistic for a favorite - typically between 1.2 and 2.0
        odds = round(random.uniform(min_odds, max_odds), 2)
        
        # Create a bet dictionary
        bet = {
            'team_name': f"{team}",
            'odds': odds,
            'sport': sport,
            'bet_id': i,
            # We'll let the algorithm calculate probabilities
        }
        
        test_bets.append(bet)
    
    return test_bets

def test_with_increasingly_favorable_odds():
    """Test with increasingly favorable odds to see at what point parlays start to appear"""
    recommender = ParlayRecommender()
    
    print("=== Testing with increasingly favorable odds ===")
    
    # Test with different max odds ranges
    odds_ranges = [
        (1.1, 1.3),  # Very low odds (heavy favorites)
        (1.2, 1.4),
        (1.3, 1.5),
        (1.4, 1.6),
        (1.5, 1.7),
        (1.7, 1.9)
    ]
    
    for min_odds, max_odds in odds_ranges:
        print(f"\nTesting with odds range: {min_odds} to {max_odds}")
        test_bets = generate_test_bets(30, min_odds, max_odds)
        
        # Show the first few test bets
        print(f"Sample bets (first 5 of {len(test_bets)}):")
        for i, bet in enumerate(test_bets[:5]):
            print(f"  Bet {i+1}: {bet['team_name']} - Odds: {bet['odds']}")
        
        # Get recommendations with debug output
        parlays = recommender.get_favorite_parlays(
            test_bets, 
            leg_count=6,
            min_odds=3.0,
            min_win_prob=50.0,
            debug=True
        )
        
        print(f"Generated {len(parlays)} 6-leg parlays")
        
        # Show details of the first parlay if any were generated
        if parlays:
            print("\nFirst parlay details:")
            parlay = parlays[0]
            print(f"  Combined odds: {parlay['decimal_odds']:.2f}")
            print(f"  Win probability: {parlay['win_probability']:.2f}%")
            print(f"  Expected value: {parlay['ev']:.2f}")
            print("  Teams:")
            for bet in parlay['bets']:
                print(f"    - {bet['team_name']} (Odds: {bet['odds']}, Sport: {bet.get('sport', 'unknown')})")

def test_with_minimum_thresholds():
    """Test with progressively lower threshold requirements"""
    recommender = ParlayRecommender()
    
    print("\n=== Testing with progressively lower thresholds ===")
    
    # Generate a fixed set of test bets
    test_bets = generate_test_bets(30, 1.2, 1.8)
    
    # Try different thresholds
    thresholds = [
        (3.0, 53.0),
        (2.5, 53.0),
        (2.0, 53.0),
        (3.0, 50.0),
        (3.0, 45.0),
        (2.0, 45.0)
    ]
    
    for min_odds, min_win_prob in thresholds:
        print(f"\nTesting with min_odds={min_odds}, min_win_prob={min_win_prob}%")
        
        parlays = recommender.get_favorite_parlays(
            test_bets, 
            leg_count=6,
            min_odds=min_odds,
            min_win_prob=min_win_prob,
            debug=True
        )
        
        print(f"Generated {len(parlays)} 6-leg parlays")
        
        if parlays:
            print("\nFirst parlay details:")
            parlay = parlays[0]
            print(f"  Combined odds: {parlay['decimal_odds']:.2f}")
            print(f"  Win probability: {parlay['win_probability']:.2f}%")
            print(f"  Expected value: {parlay['ev']:.2f}")

def analyze_probability_calculation():
    """Analyze how probability calculation works with different odds values"""
    recommender = ParlayRecommender()
    
    print("\n=== Analyzing probability calculation ===")
    
    # Test different odds values
    odds_values = [1.2, 1.3, 1.4, 1.5, 1.7, 1.9, 2.0, 2.5]
    
    print("Single bet probability estimates:")
    for odds in odds_values:
        # Create a test bet
        bet = {'odds': odds}
        # Apply probability estimation
        bets_with_prob = recommender._ensure_probabilities([bet])
        if bets_with_prob:
            implied_prob = 1 / odds
            adjusted_prob = bets_with_prob[0]['probability']
            print(f"  Odds: {odds:.2f} → Implied prob: {implied_prob:.4f} → Adjusted prob: {adjusted_prob:.4f} ({adjusted_prob*100:.1f}%)")
    
    print("\nParlay probability simulation:")
    # Test 6-leg parlays with different odds
    for odds in [1.2, 1.3, 1.4, 1.5]:
        # Create 6 identical bets
        bets = [{'odds': odds, 'team_name': f'Team{i}', 'sport': 'NBA'} for i in range(6)]
        # Apply probability estimation
        bets_with_prob = recommender._ensure_probabilities(bets)
        
        # Calculate combined probability
        if bets_with_prob:
            individual_prob = bets_with_prob[0]['probability']
            combined_prob = individual_prob ** 6  # 6 legs
            combined_odds = odds ** 6
            
            print(f"\n  Individual odds: {odds:.2f}")
            print(f"  Individual probability: {individual_prob:.4f} ({individual_prob*100:.1f}%)")
            print(f"  Combined odds (6 legs): {combined_odds:.2f}")
            print(f"  Combined probability (6 legs): {combined_prob:.6f} ({combined_prob*100:.2f}%)")
            print(f"  Meets min_odds=3.0? {combined_odds >= 3.0}")
            print(f"  Meets min_win_prob=50.0%? {combined_prob*100 >= 50.0}")
            print(f"  Criteria satisfied? {combined_odds >= 3.0 and combined_prob*100 >= 50.0}")

def test_with_final_settings():
    """Test with our final settings: 50% win probability and reduced correlation factor"""
    recommender = ParlayRecommender()
    
    print("\n=== TESTING WITH FINAL SETTINGS ===")
    print("Target criteria: min_odds = 3.0, min_win_prob = 50.0%, correlation factor = 0.01")
    
    # Generate a large set of test bets to increase chances of finding valid parlays
    test_bets = generate_test_bets(count=50, min_odds=1.2, max_odds=2.0)  # Very low odds (heavy favorites)
    
    # Run 5 attempts to verify we can consistently generate parlays
    for attempt in range(5):
        print(f"\nAttempt {attempt+1}:")
        parlays = recommender.get_favorite_parlays(test_bets, min_odds=3.0, min_win_prob=50.0, debug=True)
        
        if parlays:
            print(f"SUCCESS! Got {len(parlays)} parlays with our final settings")
            for i, parlay in enumerate(parlays):
                print(f"  Parlay {i+1}: odds={parlay['decimal_odds']:.2f}, win_prob={parlay['win_probability']:.2f}%")
        else:
            print("No parlays found in this attempt")
            
def main():
    print("=== Favorite Parlay Recommendations Test ===")
    
    # Test with increasingly favorable odds
    test_with_increasingly_favorable_odds()
    
    # Test with different thresholds
    test_with_minimum_thresholds()
    
    # Analyze probability calculation
    analyze_probability_calculation()
    
    # Test with final settings
    test_with_final_settings()

if __name__ == "__main__":
    main()