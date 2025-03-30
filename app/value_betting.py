"""
BettingBuddy Value Betting Module

This module implements value betting algorithms to identify bets with positive expected value.
"""

import math
from typing import List, Dict, Tuple, Optional, Any, Union
from models import Bet, Parlay, Team, Sport
from database import american_to_decimal, decimal_to_american

class ValueBettingAnalyzer:
    """
    Analyzer for identifying value bets with positive expected value (EV).
    """
    
    def __init__(self):
        self.confidence_threshold = 0.6  # 60% confidence threshold
        self.min_edge = 0.05  # Minimum 5% edge for a value bet
        
    def set_params(self, confidence_threshold=None, min_edge=None):
        """
        Update analyzer parameters.
        
        Args:
            confidence_threshold (float, optional): Minimum confidence level (0.0-1.0)
            min_edge (float, optional): Minimum edge percentage (0.0-1.0)
        """
        if confidence_threshold is not None:
            self.confidence_threshold = max(0.0, min(1.0, confidence_threshold))
            
        if min_edge is not None:
            self.min_edge = max(0.0, min(1.0, min_edge))
    
    def analyze_odds(self, bookmaker_odds: str, true_probability: float) -> Dict[str, Any]:
        """
        Analyze a bet for its value.
        
        Args:
            bookmaker_odds (str): Bookmaker odds in American format
            true_probability (float): Your estimated true probability of winning (0.0-1.0)
            
        Returns:
            Dict: Analysis results with keys:
                - is_value_bet (bool): True if this is a value bet
                - ev (float): Expected value (%)
                - edge (float): Edge percentage
                - fair_odds (str): Fair odds based on true probability
                - confidence (float): Confidence score
        """
        # Calculate implied probability from bookmaker odds
        decimal_odds = american_to_decimal(bookmaker_odds)
        implied_prob = 1 / decimal_odds
        
        # Calculate fair odds from true probability
        fair_decimal_odds = 1 / true_probability if true_probability > 0 else 100
        fair_american_odds = decimal_to_american(fair_decimal_odds)
        
        # Calculate edge
        edge = true_probability - implied_prob
        
        # Calculate expected value
        ev = (decimal_odds * true_probability) - 1
        
        # Determine if this is a value bet
        is_value_bet = (edge >= self.min_edge and true_probability >= self.confidence_threshold)
        
        # Calculate confidence score (higher number is better)
        # Accounts for both probability and edge
        confidence = true_probability * (1 + edge)
        
        return {
            'is_value_bet': is_value_bet,
            'ev': ev * 100,  # Convert to percentage
            'edge': edge * 100,  # Convert to percentage
            'fair_odds': fair_american_odds,
            'confidence': confidence
        }
    
    def find_best_value_bets(self, bets_data: List[Dict[str, Any]], max_bets=5) -> List[Dict[str, Any]]:
        """
        Find the best value bets from a list of potential bets.
        
        Args:
            bets_data (List[Dict]): List of potential bets with keys:
                - team_name: Team name
                - odds: Bookmaker odds in American format
                - true_probability: Your estimated true probability (0.0-1.0)
            max_bets (int): Maximum number of bets to return
                
        Returns:
            List[Dict]: List of best value bets with analysis data
        """
        analyzed_bets = []
        
        for bet in bets_data:
            if 'true_probability' not in bet or 'odds' not in bet:
                continue
                
            analysis = self.analyze_odds(bet['odds'], bet['true_probability'])
            
            # Add bet data to analysis
            analysis.update({
                'team_name': bet.get('team_name', 'Unknown'),
                'odds': bet['odds'],
                'true_probability': bet['true_probability'],
                'sport': bet.get('sport', 'Unknown'),
                'event_date': bet.get('event_date')
            })
            
            analyzed_bets.append(analysis)
        
        # Sort by confidence score in descending order
        analyzed_bets.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Filter to value bets only
        value_bets = [b for b in analyzed_bets if b['is_value_bet']]
        
        # Return top N value bets
        return value_bets[:max_bets]
    
    def kelly_criterion(self, odds: str, true_probability: float, 
                        fraction: float = 1.0) -> float:
        """
        Calculate the optimal bet size using the Kelly Criterion.
        
        Args:
            odds (str): Bookmaker odds in American format
            true_probability (float): Your estimated true probability (0.0-1.0)
            fraction (float): Kelly fraction to reduce volatility (0.0-1.0)
            
        Returns:
            float: Optimal bet size as a fraction of bankroll
        """
        decimal_odds = american_to_decimal(odds)
        b = decimal_odds - 1  # Decimal odds minus 1
        q = 1 - true_probability  # Probability of losing
        
        # Kelly formula: (bp - q) / b
        # Where b = decimal odds - 1, p = probability of winning, q = probability of losing
        kelly = (b * true_probability - q) / b if b > 0 else 0
        
        # Apply Kelly fraction to reduce volatility
        kelly = kelly * fraction
        
        # Cap at max 20% of bankroll as a safety measure
        return min(kelly, 0.2)
    
    def suggest_parlay(self, value_bets: List[Dict[str, Any]], 
                      max_legs=3, min_correlation=-0.2) -> Dict[str, Any]:
        """
        Suggest a parlay from value bets, considering correlation.
        
        Args:
            value_bets (List[Dict]): List of value bets with analysis data
            max_legs (int): Maximum number of legs in the parlay
            min_correlation (float): Minimum correlation threshold
            
        Returns:
            Dict: Parlay suggestion with bets and analysis
        """
        if not value_bets or len(value_bets) < 2:
            return None
            
        # Sort bets by EV
        sorted_bets = sorted(value_bets, key=lambda x: x['ev'], reverse=True)
        
        # Take top bets with low correlation
        parlay_bets = []
        parlay_bets.append(sorted_bets[0])  # Always add the best bet
        
        for bet in sorted_bets[1:]:
            # Simple correlation check - different sports have low correlation
            # In a real implementation, you would use actual correlation data
            if len(parlay_bets) < max_legs:
                # Check if the bet is from a different sport than existing bets
                different_sport = all(bet.get('sport') != existing.get('sport') 
                                    for existing in parlay_bets)
                
                if different_sport:
                    parlay_bets.append(bet)
        
        if len(parlay_bets) < 2:
            return None  # Need at least 2 legs for a parlay
            
        # Calculate combined probability and odds
        combined_prob = 1.0
        for bet in parlay_bets:
            combined_prob *= bet['true_probability']
            
        fair_decimal_odds = 1 / combined_prob if combined_prob > 0 else 100
        fair_american_odds = decimal_to_american(fair_decimal_odds)
        
        # Calculate parlay's decimal odds
        parlay_decimal_odds = 1.0
        for bet in parlay_bets:
            parlay_decimal_odds *= american_to_decimal(bet['odds'])
            
        parlay_american_odds = decimal_to_american(parlay_decimal_odds)
        
        # Calculate expected value
        ev = (parlay_decimal_odds * combined_prob) - 1
        
        return {
            'bets': parlay_bets,
            'combined_probability': combined_prob,
            'fair_odds': fair_american_odds,
            'bookmaker_odds': parlay_american_odds,
            'ev': ev * 100,  # Convert to percentage
            'is_value_parlay': ev > 0
        }
    
    def calculate_true_probability(self, historical_data: List[Dict[str, Any]], 
                                  model_probability: float) -> float:
        """
        Calculate a true probability estimate by combining model and historical data.
        
        Args:
            historical_data (List[Dict]): Historical performance data
            model_probability (float): Probability from predictive model
            
        Returns:
            float: Adjusted true probability
        """
        # In a real implementation, this would be a sophisticated model
        # For simplicity, we'll use a weighted average approach
        
        if not historical_data:
            return model_probability
            
        # Calculate historical win rate
        total_matches = len(historical_data)
        wins = sum(1 for match in historical_data if match.get('result') == 'win')
        historical_prob = wins / total_matches if total_matches > 0 else 0.5
        
        # Calculate weight based on sample size
        # More historical data = more weight
        max_weight = 0.7
        weight = min(total_matches / 20, max_weight)
        
        # Combine probabilities
        true_prob = (weight * historical_prob) + ((1 - weight) * model_probability)
        
        # Ensure probability is between 0 and 1
        return max(0.0, min(1.0, true_prob))


class ValueBettingStrategy:
    """
    Strategy for implementing value betting in practice.
    """
    
    def __init__(self, analyzer=None):
        """
        Initialize the value betting strategy.
        
        Args:
            analyzer (ValueBettingAnalyzer, optional): Custom analyzer instance
        """
        self.analyzer = analyzer or ValueBettingAnalyzer()
        self.bankroll_management = 'kelly'  # 'kelly', 'flat', or 'percentage'
        self.stake_percentage = 0.02  # 2% of bankroll for flat betting
        self.kelly_fraction = 0.5  # Half-Kelly for reduced volatility
    
    def set_bankroll_strategy(self, strategy='kelly', stake_percentage=0.02, 
                             kelly_fraction=0.5):
        """
        Set the bankroll management strategy.
        
        Args:
            strategy (str): 'kelly', 'flat', or 'percentage'
            stake_percentage (float): Percentage of bankroll for flat betting
            kelly_fraction (float): Kelly fraction for reduced volatility
        """
        self.bankroll_management = strategy
        self.stake_percentage = max(0.01, min(0.1, stake_percentage))
        self.kelly_fraction = max(0.1, min(1.0, kelly_fraction))
    
    def calculate_bet_size(self, bankroll: float, odds: str, true_probability: float) -> float:
        """
        Calculate bet size based on bankroll management strategy.
        
        Args:
            bankroll (float): Current bankroll amount
            odds (str): Bookmaker odds in American format
            true_probability (float): Estimated true probability
            
        Returns:
            float: Recommended bet size
        """
        if self.bankroll_management == 'kelly':
            kelly_pct = self.analyzer.kelly_criterion(
                odds, true_probability, self.kelly_fraction
            )
            return bankroll * kelly_pct
            
        elif self.bankroll_management == 'flat':
            return bankroll * self.stake_percentage
            
        elif self.bankroll_management == 'percentage':
            # Adjust percentage based on edge
            analysis = self.analyzer.analyze_odds(odds, true_probability)
            edge_factor = 1.0 + (analysis['edge'] / 100)
            adjusted_pct = self.stake_percentage * edge_factor
            return bankroll * min(adjusted_pct, 0.1)  # Cap at 10%
        
        # Default to flat betting
        return bankroll * self.stake_percentage
    
    def generate_betting_plan(self, bankroll: float, available_bets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive betting plan.
        
        Args:
            bankroll (float): Current bankroll amount
            available_bets (List[Dict]): Available bets with odds and probabilities
            
        Returns:
            Dict: Betting plan with recommendations
        """
        # Find value bets
        value_bets = self.analyzer.find_best_value_bets(available_bets)
        
        # Calculate bet sizes
        for bet in value_bets:
            bet_size = self.calculate_bet_size(
                bankroll, bet['odds'], bet['true_probability']
            )
            bet['recommended_stake'] = round(bet_size, 2)
            bet['percentage_of_bankroll'] = (bet_size / bankroll) * 100
        
        # Generate parlay suggestion
        parlay_suggestion = self.analyzer.suggest_parlay(value_bets)
        
        # Calculate parlay stake if it's a value parlay
        if parlay_suggestion and parlay_suggestion.get('is_value_parlay'):
            parlay_stake = bankroll * 0.01  # Use 1% of bankroll for parlays
            parlay_suggestion['recommended_stake'] = round(parlay_stake, 2)
        
        return {
            'value_bets': value_bets,
            'parlay_suggestion': parlay_suggestion,
            'total_recommended_exposure': sum(bet.get('recommended_stake', 0) 
                                            for bet in value_bets),
            'bankroll': bankroll
        }