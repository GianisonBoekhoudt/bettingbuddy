#!/usr/bin/env python3
"""
Parlay Recommendations Module for BettingBuddy app.

Analyzes odds and provides recommendations for valuable parlays.
"""

import math
import itertools
from datetime import datetime, timedelta

class ParlayRecommender:
    """
    Analyzes bets and provides parlay recommendations based on various strategies.
    """
    
    def __init__(self):
        """Initialize the ParlayRecommender."""
        # Configuration for different parlay types
        self.config = {
            'single_bets': {
                'min_odds': 2.0,         # Minimum decimal odds for single bets
                'min_win_prob': 80.0,    # Minimum win probability (%)
                'max_results': 5         # Maximum number of results to return
            },
            'two_leg_parlays': {
                'min_odds': 4.0,        # Minimum total decimal odds
                'min_win_prob': 60.0,   # Minimum win probability (%)
                'max_results': 3,       # Maximum number of results to return
                'max_legs': 2           # Number of bets in the parlay
            },
            'three_leg_parlays': {
                'min_odds': 5.0,        # Minimum total decimal odds
                'min_win_prob': 40.0,   # Minimum win probability (%)
                'max_results': 3,       # Maximum number of results to return
                'max_legs': 3           # Number of bets in the parlay
            },
            'favorite_parlays': {
                'min_odds': 3.0,        # Minimum total decimal odds
                'min_win_prob': 50.0,   # Minimum win probability (%)
                'max_results': 2,       # Maximum number of results to return
                'max_legs': 6,          # Maximum number of bets in the parlay
                'max_odds_per_leg': 1.5  # Maximum decimal odds per leg (favorites)
            }
        }
    
    def american_to_decimal(self, american_odds):
        """
        Convert American odds format to decimal.
        
        Args:
            american_odds (str): Odds in American format (e.g., +120, -110)
            
        Returns:
            float: Odds in decimal format
        """
        try:
            if american_odds.startswith('+'):
                odds_value = int(american_odds[1:])
                return (odds_value / 100) + 1
            else:  # Negative odds
                odds_value = int(american_odds[1:])
                return (100 / odds_value) + 1
        except (ValueError, ZeroDivisionError):
            return 1.0  # Default to even odds on error
    
    def calculate_win_probability(self, american_odds):
        """
        Calculate implied probability of winning from American odds.
        
        Args:
            american_odds (str): Odds in American format
            
        Returns:
            float: Win probability as a percentage
        """
        try:
            if american_odds.startswith('+'):
                odds_value = int(american_odds[1:])
                return 100 / (odds_value + 100) * 100
            else:  # Negative odds
                odds_value = int(american_odds[1:])
                return odds_value / (odds_value + 100) * 100
        except (ValueError, ZeroDivisionError):
            return 50.0  # Default to 50% on error
    
    def decimal_to_american(self, decimal_odds):
        """
        Convert decimal odds to American format.
        
        Args:
            decimal_odds (float): Odds in decimal format
            
        Returns:
            str: Odds in American format
        """
        if decimal_odds >= 2.0:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"
    
    def get_single_bet_recommendations(self, bets):
        """
        Get recommendations for single (straight) bets.
        
        Args:
            bets (list): List of bet dictionaries
            
        Returns:
            list: List of recommended bets
        """
        config = self.config['single_bets']
        recommendations = []
        
        # Process each bet
        for bet in bets:
            decimal_odds = self.american_to_decimal(bet['odds'])
            win_probability = self.calculate_win_probability(bet['odds'])
            
            # Check if bet meets criteria
            if decimal_odds >= config['min_odds'] and win_probability >= config['min_win_prob']:
                # Create a recommendation with additional data
                recommendation = bet.copy()
                recommendation['decimal_odds'] = decimal_odds
                recommendation['win_probability'] = win_probability
                recommendation['expected_value'] = (win_probability / 100 * decimal_odds) - 1
                recommendation['recommendation_type'] = 'single'
                
                recommendations.append(recommendation)
        
        # Sort by expected value descending
        recommendations.sort(key=lambda x: x['expected_value'], reverse=True)
        
        # Return top N results
        return recommendations[:config['max_results']]
    
    def get_parlay_recommendations(self, bets, config_key):
        """
        Get recommendations for parlays based on configuration.
        
        Args:
            bets (list): List of bet dictionaries
            config_key (str): Configuration key (e.g., 'two_leg_parlays')
            
        Returns:
            list: List of recommended parlays
        """
        config = self.config[config_key]
        recommendations = []
        
        # Special handling for favorite parlays
        if config_key == 'favorite_parlays':
            # Filter to only include heavy favorites
            favorites = []
            for bet in bets:
                decimal_odds = self.american_to_decimal(bet['odds'])
                if decimal_odds <= config['max_odds_per_leg']:
                    bet_copy = bet.copy()
                    bet_copy['decimal_odds'] = decimal_odds
                    bet_copy['win_probability'] = self.calculate_win_probability(bet['odds'])
                    favorites.append(bet_copy)
            
            # Sort by win probability (highest first)
            favorites.sort(key=lambda x: x['win_probability'], reverse=True)
            
            # Get top N favorites up to max_legs
            top_favorites = favorites[:config['max_legs']]
            
            # If we have enough favorites, create a parlay
            if len(top_favorites) >= 2:
                # Calculate combined odds and probability
                decimal_odds = 1.0
                for bet in top_favorites:
                    decimal_odds *= bet['decimal_odds']
                
                win_probability = 1.0
                for bet in top_favorites:
                    win_probability *= (bet['win_probability'] / 100)
                
                # Convert to percentage
                win_probability *= 100
                
                # Check if parlay meets criteria
                if decimal_odds >= config['min_odds'] and win_probability >= config['min_win_prob']:
                    # Create parlay recommendation
                    american_odds = self.decimal_to_american(decimal_odds)
                    expected_value = (win_probability / 100 * decimal_odds) - 1
                    
                    recommendation = {
                        'bets': top_favorites,
                        'decimal_odds': decimal_odds,
                        'american_odds': american_odds,
                        'win_probability': win_probability,
                        'expected_value': expected_value,
                        'recommendation_type': config_key,
                        'leg_count': len(top_favorites)
                    }
                    
                    recommendations.append(recommendation)
            
            return recommendations[:config['max_results']]
        else:
            # Standard parlay processing for 2-leg and 3-leg parlays
            max_legs = config['max_legs']
            
            # Get all combinations of bets for the parlay
            for combo in itertools.combinations(bets, max_legs):
                # Calculate combined odds and probability
                decimal_odds = 1.0
                for bet in combo:
                    decimal_odds *= self.american_to_decimal(bet['odds'])
                
                win_probability = 1.0
                for bet in combo:
                    win_probability *= (self.calculate_win_probability(bet['odds']) / 100)
                
                # Convert to percentage
                win_probability *= 100
                
                # Check if parlay meets criteria
                if decimal_odds >= config['min_odds'] and win_probability >= config['min_win_prob']:
                    # Create parlay recommendation
                    american_odds = self.decimal_to_american(decimal_odds)
                    expected_value = (win_probability / 100 * decimal_odds) - 1
                    
                    # Create copies of bets with additional data
                    parlay_bets = []
                    for bet in combo:
                        bet_copy = bet.copy()
                        bet_copy['decimal_odds'] = self.american_to_decimal(bet['odds'])
                        bet_copy['win_probability'] = self.calculate_win_probability(bet['odds'])
                        parlay_bets.append(bet_copy)
                    
                    recommendation = {
                        'bets': parlay_bets,
                        'decimal_odds': decimal_odds,
                        'american_odds': american_odds,
                        'win_probability': win_probability,
                        'expected_value': expected_value,
                        'recommendation_type': config_key,
                        'leg_count': len(combo)
                    }
                    
                    recommendations.append(recommendation)
            
            # Sort by expected value descending
            recommendations.sort(key=lambda x: x['expected_value'], reverse=True)
            
            # Return top N results
            return recommendations[:config['max_results']]
    
    def get_all_recommendations(self, bets):
        """
        Get all types of recommendations.
        
        Args:
            bets (list): List of bet dictionaries
            
        Returns:
            dict: Dictionary with different recommendation types
        """
        # Make sure bets have the required fields
        valid_bets = []
        for bet in bets:
            if 'odds' in bet and 'team_name' in bet:
                valid_bets.append(bet)
        
        if not valid_bets:
            return {
                'single_bets': [],
                'two_leg_parlays': [],
                'three_leg_parlays': [],
                'favorite_parlays': []
            }
        
        recommendations = {
            'single_bets': self.get_single_bet_recommendations(valid_bets),
            'two_leg_parlays': self.get_parlay_recommendations(valid_bets, 'two_leg_parlays'),
            'three_leg_parlays': self.get_parlay_recommendations(valid_bets, 'three_leg_parlays'),
            'favorite_parlays': self.get_parlay_recommendations(valid_bets, 'favorite_parlays')
        }
        
        return recommendations
    
    def get_recommendations_by_sport(self, bets, sport_id=None):
        """
        Get recommendations filtered by sport.
        
        Args:
            bets (list): List of bet dictionaries
            sport_id (int, optional): Sport ID to filter by
            
        Returns:
            dict: Dictionary with different recommendation types
        """
        if sport_id:
            # Filter bets by sport ID
            filtered_bets = [bet for bet in bets if bet.get('sport_id') == sport_id]
            return self.get_all_recommendations(filtered_bets)
        else:
            # No filtering
            return self.get_all_recommendations(bets)
