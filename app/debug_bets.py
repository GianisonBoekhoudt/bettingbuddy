"""
Debug Active Bets

This script checks the active bets and prints their details.
"""

from models import Bet
from parlay_recommendations import ParlayRecommender

def print_active_bets():
    bets = Bet.get_active_bets(limit=10)
    print(f'Active bets: {len(bets)}')
    
    for i, bet in enumerate(bets):
        print(f'Bet {i+1}:')
        print(f'  ID: {bet.id}')
        print(f'  Team: {bet.team_name}')
        print(f'  Sport: {bet.sport_name}')
        print(f'  Odds: {bet.odds}')
        print(f'  Status: {bet.status}')
        print(f'  Description: {bet.description}')
        print()

def check_recommendations():
    print("Creating ParlayRecommender...")
    pr = ParlayRecommender()
    
    print("Getting active bets for manual recommendation...")
    bets = Bet.get_active_bets(limit=30)
    
    # Convert to dictionaries for the recommender
    bet_dicts = []
    for bet in bets:
        bet_dict = {
            'team_name': bet.team_name,
            'odds': bet.odds,
            'sport': bet.sport_name,
            'bet_id': bet.id
        }
        bet_dicts.append(bet_dict)
    
    print(f"Converted {len(bet_dicts)} bets to dictionaries")
    
    # Try making recommendations manually
    if len(bet_dicts) >= 2:
        print("\nTrying to manually create a 2-leg parlay...")
        two_leg = pr.get_two_leg_parlays(bet_dicts)
        print(f"Manually created 2-leg parlays: {len(two_leg)}")
        
        # If no parlays, let's debug why
        if len(two_leg) == 0:
            print("Debugging why no 2-leg parlays were created:")
            for i, bet1 in enumerate(bet_dicts):
                for j, bet2 in enumerate(bet_dicts[i+1:], i+1):
                    if bet1['sport'] == bet2['sport']:
                        print(f"Same sport: {bet1['team_name']} and {bet2['team_name']}")
                    try:
                        # The odds are already in decimal format (like '+1.93')
                        # So we just need to convert to float
                        decimal_odds1 = float(bet1['odds'])
                        decimal_odds2 = float(bet2['odds'])
                        combined_odds = decimal_odds1 * decimal_odds2
                        win_prob = (1 / decimal_odds1) * (1 / decimal_odds2) * 100
                        print(f"  {bet1['team_name']} ({bet1['odds']}) + {bet2['team_name']} ({bet2['odds']}):")
                        print(f"  Combined odds: {combined_odds:.2f}, Win prob: {win_prob:.2f}%")
                        # Apply our new thresholds
                        if combined_odds < 1.5:
                            print(f"  Combined odds too low: {combined_odds:.2f} < 1.5")
                        if win_prob < 60:
                            print(f"  Win probability too low: {win_prob:.2f}% < 60%")
                    except Exception as e:
                        print(f"  Error calculating for {bet1['team_name']} + {bet2['team_name']}: {e}")
    
    if len(bet_dicts) >= 3:
        print("\nTrying to manually create a 3-leg parlay...")
        three_leg = pr.get_three_leg_parlays(bet_dicts)
        print(f"Manually created 3-leg parlays: {len(three_leg)}")
    
    print("\nGetting recommendations from models...")
    recs = pr.get_recommendations_from_models()
    
    print(f'Two-leg parlays: {len(recs["two_leg_parlays"])}')
    print(f'Three-leg parlays: {len(recs["three_leg_parlays"])}')
    print(f'Favorite parlays: {len(recs["favorite_parlays"])}')
    
    # If we have some recommendations, let's print details of the first one
    for parlay_type, parlays in recs.items():
        if parlays:
            print(f"\nFirst {parlay_type} parlay:")
            parlay = parlays[0]
            print(f"  Decimal Odds: {parlay['decimal_odds']}")
            print(f"  American Odds: {parlay['american_odds']}")
            print(f"  Win Probability: {parlay['win_probability']:.2f}%")
            print(f"  Expected Value: {parlay['ev']:.2f}")
            
            print("  Bets:")
            for bet in parlay['bets']:
                print(f"    - {bet['team_name']} ({bet['odds']})")

if __name__ == "__main__":
    print("==== Active Bets ====")
    print_active_bets()
    
    print("\n==== Parlay Recommendations ====")
    check_recommendations()