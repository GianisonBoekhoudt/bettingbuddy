"""
Test script for parlay recommendations
"""
import random
from parlay_recommendations import ParlayRecommender

def test_multiple_bets():
    # Set a fixed seed for reproducible results
    random.seed(42)
    
    # Create a recommender
    recommender = ParlayRecommender()
    
    # Create test bets from different sports
    sports = ['MMA', 'NBA', 'NFL', 'MLB', 'NHL']
    bets = []
    
    # Create 10 bets with different odds
    for i in range(10):
        # Alternate between odds of 3.0 (qualifying for single bets) and 2.0
        odds = 3.0 if i % 2 == 0 else 2.0
        bet = {
            'team_name': f'Team {i}',
            'odds': str(odds),
            'sport': sports[i % len(sports)]
        }
        bets.append(bet)
        
    print('Testing regular parlay recommendations with 10 mixed-odds bets from different sports')
    
    # Get all recommendations
    results = recommender.get_all_recommendations(bets)
    
    # Print the count of recommendations for each type
    for key, value in results.items():
        print(f'{key}: {len(value)} recommendations')
        
    # Print details of each recommendation type
    print("\nSingle bet recommendations:")
    for rec in results.get('single_bets', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nTwo-leg parlay recommendations:")
    for rec in results.get('two_leg_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nThree-leg parlay recommendations:")
    for rec in results.get('three_leg_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nFavorite parlay recommendations:")
    for rec in results.get('favorite_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
        
def test_favorite_parlays():
    # Set a fixed seed for reproducible results
    random.seed(42)
    
    # Create a recommender
    recommender = ParlayRecommender()
    
    # Create test bets from different sports with high enough odds for favorite parlays
    sports = ['MMA', 'NBA', 'NFL', 'MLB', 'NHL']
    bets = []
    
    # Create 20 bets with different odds
    for i in range(20):
        # Use higher odds for favorite parlays test (1.35-1.4)
        # These lower odds qualify for favorites since they imply higher probability
        odds = 1.35 + (i % 2) * 0.05  # 1.35, 1.4 for higher probabilities
        bet = {
            'team_name': f'Favorite {i}',
            'odds': str(odds),
            'sport': sports[i % len(sports)]
        }
        bets.append(bet)
    
    print('Testing favorite parlay recommendations with 20 low-odds bets from different sports')
    
    # Get all recommendations
    results = recommender.get_all_recommendations(bets)
    
    # Print the count of recommendations for each type
    for key, value in results.items():
        print(f'{key}: {len(value)} recommendations')
        
    # Print details of each recommendation type
    print("\nSingle bet recommendations:")
    for rec in results.get('single_bets', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nTwo-leg parlay recommendations:")
    for rec in results.get('two_leg_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nThree-leg parlay recommendations:")
    for rec in results.get('three_leg_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")
    
    print("\nFavorite parlay recommendations:")
    for rec in results.get('favorite_parlays', []):
        teams = [bet['team_name'] for bet in rec['bets']]
        print(f"  Teams: {teams}, Odds: {rec['decimal_odds']}, Win Prob: {rec['win_probability']:.2f}%")

if __name__ == "__main__":
    print("\n=== TESTING REGULAR PARLAY RECOMMENDATIONS ===\n")
    test_multiple_bets()
    
    print("\n\n=== TESTING FAVORITE PARLAY RECOMMENDATIONS ===\n")
    test_favorite_parlays()