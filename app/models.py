#!/usr/bin/env python3
"""
Models for BettingBuddy app.

Defines data models and business logic for the betting app.
"""

from datetime import datetime
import json

class Sport:
    """
    Represents a sport in the system.
    """
    
    def __init__(self, sport_id=None, name=None, api_id=None, active=True, icon_path=None):
        """
        Initialize a Sport object.
        
        Args:
            sport_id (int, optional): Sport ID
            name (str, optional): Sport name
            api_id (str, optional): API identifier for the sport
            active (bool, optional): Whether the sport is active
            icon_path (str, optional): Path to the sport's icon
        """
        self.id = sport_id
        self.name = name
        self.api_id = api_id
        self.active = active
        self.icon_path = icon_path
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Sport object from a dictionary.
        
        Args:
            data (dict): Dictionary with sport data
            
        Returns:
            Sport: Sport object
        """
        return cls(
            sport_id=data.get('id'),
            name=data.get('name'),
            api_id=data.get('api_id'),
            active=bool(data.get('active', 1)),
            icon_path=data.get('icon_path')
        )
    
    def to_dict(self):
        """
        Convert Sport object to dictionary.
        
        Returns:
            dict: Dictionary representation of the sport
        """
        return {
            'id': self.id,
            'name': self.name,
            'api_id': self.api_id,
            'active': 1 if self.active else 0,
            'icon_path': self.icon_path
        }


class Team:
    """
    Represents a team in the system.
    """
    
    def __init__(self, team_id=None, name=None, sport_id=None, api_id=None, logo_path=None):
        """
        Initialize a Team object.
        
        Args:
            team_id (int, optional): Team ID
            name (str, optional): Team name
            sport_id (int, optional): Sport ID this team belongs to
            api_id (str, optional): API identifier for the team
            logo_path (str, optional): Path to the team's logo
        """
        self.id = team_id
        self.name = name
        self.sport_id = sport_id
        self.api_id = api_id
        self.logo_path = logo_path
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Team object from a dictionary.
        
        Args:
            data (dict): Dictionary with team data
            
        Returns:
            Team: Team object
        """
        return cls(
            team_id=data.get('id'),
            name=data.get('name'),
            sport_id=data.get('sport_id'),
            api_id=data.get('api_id'),
            logo_path=data.get('logo_path')
        )
    
    def to_dict(self):
        """
        Convert Team object to dictionary.
        
        Returns:
            dict: Dictionary representation of the team
        """
        return {
            'id': self.id,
            'name': self.name,
            'sport_id': self.sport_id,
            'api_id': self.api_id,
            'logo_path': self.logo_path
        }


class Bet:
    """
    Represents a bet in the system.
    """
    
    def __init__(self, bet_id=None, team_id=None, odds=None, description=None, event_date=None,
                created_at=None, status="pending", result=None, active=True, 
                commence_time=None, sport_name=None, team_name=None):
        """
        Initialize a Bet object.
        
        Args:
            bet_id (int, optional): Bet ID
            team_id (int, optional): Team ID this bet is for
            odds (str, optional): Betting odds
            description (str, optional): Bet description
            event_date (str, optional): Event date/time
            created_at (str, optional): Creation date/time
            status (str, optional): Bet status (pending, won, lost)
            result (str, optional): Bet result
            active (bool, optional): Whether the bet is active
            commence_time (str, optional): Event start time
            sport_name (str, optional): Sport name
            team_name (str, optional): Team name
        """
        self.id = bet_id
        self.team_id = team_id
        self.odds = odds
        self.description = description
        self.event_date = event_date
        self.created_at = created_at or datetime.now().isoformat()
        self.status = status
        self.result = result
        self.active = active
        self.commence_time = commence_time
        self.sport_name = sport_name
        self.team_name = team_name
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Bet object from a dictionary.
        
        Args:
            data (dict): Dictionary with bet data
            
        Returns:
            Bet: Bet object
        """
        return cls(
            bet_id=data.get('id'),
            team_id=data.get('team_id'),
            odds=data.get('odds'),
            description=data.get('description'),
            event_date=data.get('event_date'),
            created_at=data.get('created_at'),
            status=data.get('status', 'pending'),
            result=data.get('result'),
            active=bool(data.get('active', 1)),
            commence_time=data.get('commence_time'),
            sport_name=data.get('sport_name'),
            team_name=data.get('team_name')
        )
    
    def to_dict(self):
        """
        Convert Bet object to dictionary.
        
        Returns:
            dict: Dictionary representation of the bet
        """
        return {
            'id': self.id,
            'team_id': self.team_id,
            'odds': self.odds,
            'description': self.description,
            'event_date': self.event_date,
            'created_at': self.created_at,
            'status': self.status,
            'result': self.result,
            'active': 1 if self.active else 0,
            'commence_time': self.commence_time,
            'sport_name': self.sport_name,
            'team_name': self.team_name
        }
    
    def calculate_win_probability(self):
        """
        Calculate the implied probability of winning based on odds.
        
        Returns:
            float: Win probability as a percentage
        """
        try:
            # Convert to American odds first
            if self.odds.startswith('+'):
                american_odds = int(self.odds[1:])
                implied_prob = 100 / (american_odds + 100)
            else:  # Negative odds
                american_odds = int(self.odds[1:])
                implied_prob = american_odds / (american_odds + 100)
            
            # Return as percentage
            return implied_prob * 100
        except (ValueError, ZeroDivisionError):
            return 0


class Parlay:
    """
    Represents a parlay (multiple bets) in the system.
    """
    
    def __init__(self, parlay_id=None, stake=0, total_odds=None, potential_payout=0,
                created_at=None, status="pending", notes=None, bets=None):
        """
        Initialize a Parlay object.
        
        Args:
            parlay_id (int, optional): Parlay ID
            stake (float, optional): Stake amount
            total_odds (str, optional): Total parlay odds
            potential_payout (float, optional): Potential payout
            created_at (str, optional): Creation date/time
            status (str, optional): Parlay status (pending, won, lost)
            notes (str, optional): Parlay notes
            bets (list, optional): List of Bet objects in the parlay
        """
        self.id = parlay_id
        self.stake = stake
        self.total_odds = total_odds
        self.potential_payout = potential_payout
        self.created_at = created_at or datetime.now().isoformat()
        self.status = status
        self.notes = notes
        self.bets = bets or []
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Parlay object from a dictionary.
        
        Args:
            data (dict): Dictionary with parlay data
            
        Returns:
            Parlay: Parlay object
        """
        bets = []
        if 'bets' in data:
            for bet_data in data['bets']:
                bets.append(Bet.from_dict(bet_data))
        
        return cls(
            parlay_id=data.get('id'),
            stake=float(data.get('stake', 0)),
            total_odds=data.get('total_odds'),
            potential_payout=float(data.get('potential_payout', 0)),
            created_at=data.get('created_at'),
            status=data.get('status', 'pending'),
            notes=data.get('notes'),
            bets=bets
        )
    
    def to_dict(self):
        """
        Convert Parlay object to dictionary.
        
        Returns:
            dict: Dictionary representation of the parlay
        """
        return {
            'id': self.id,
            'stake': self.stake,
            'total_odds': self.total_odds,
            'potential_payout': self.potential_payout,
            'created_at': self.created_at,
            'status': self.status,
            'notes': self.notes,
            'bets': [bet.to_dict() for bet in self.bets] if self.bets else []
        }
    
    def add_bet(self, bet):
        """
        Add a bet to the parlay.
        
        Args:
            bet (Bet): Bet to add
        """
        self.bets.append(bet)
        
        # Recalculate total odds and potential payout
        self.calculate_totals()
    
    def remove_bet(self, bet_id):
        """
        Remove a bet from the parlay.
        
        Args:
            bet_id (int): ID of bet to remove
            
        Returns:
            bool: True if bet was removed, False otherwise
        """
        for i, bet in enumerate(self.bets):
            if bet.id == bet_id:
                self.bets.pop(i)
                
                # Recalculate total odds and potential payout
                self.calculate_totals()
                return True
        
        return False
    
    def calculate_totals(self):
        """
        Calculate total odds and potential payout for the parlay.
        """
        # Start with 1.0 for decimal odds computation
        decimal_odds = 1.0
        
        for bet in self.bets:
            # Convert American odds to decimal
            if bet.odds.startswith('+'):
                american_odds = int(bet.odds[1:])
                leg_decimal = (american_odds / 100) + 1
            else:  # Negative odds
                american_odds = int(bet.odds[1:])
                leg_decimal = (100 / american_odds) + 1
            
            # Multiply to get parlay decimal odds
            decimal_odds *= leg_decimal
        
        # Convert back to American odds
        if decimal_odds > 2.0:
            american_odds = f"+{int((decimal_odds - 1) * 100)}"
        else:
            american_odds = f"-{int(100 / (decimal_odds - 1))}"
        
        self.total_odds = american_odds
        
        # Calculate potential payout
        self.potential_payout = self.stake * decimal_odds
    
    def calculate_win_probability(self):
        """
        Calculate the estimated win probability of the entire parlay.
        
        Returns:
            float: Win probability as a percentage
        """
        # Start with 100% and multiply by each bet's probability
        probability = 1.0
        
        for bet in self.bets:
            bet_prob = bet.calculate_win_probability() / 100
            probability *= bet_prob
        
        # Return as percentage
        return probability * 100


class UserPreferences:
    """
    Represents user preferences in the system.
    """
    
    def __init__(self, pref_id=None, odds_format="american", theme="light", 
                notification_enabled=True, api_key=None, preferences=None):
        """
        Initialize a UserPreferences object.
        
        Args:
            pref_id (int, optional): Preference ID
            odds_format (str, optional): Odds format (american, decimal, fractional)
            theme (str, optional): UI theme (light, dark)
            notification_enabled (bool, optional): Whether notifications are enabled
            api_key (str, optional): API key
            preferences (dict, optional): Additional preferences
        """
        self.id = pref_id
        self.odds_format = odds_format
        self.theme = theme
        self.notification_enabled = notification_enabled
        self.api_key = api_key
        self.preferences = preferences or {}
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a UserPreferences object from a dictionary.
        
        Args:
            data (dict): Dictionary with preference data
            
        Returns:
            UserPreferences: UserPreferences object
        """
        prefs = {}
        if 'preferences' in data and data['preferences']:
            try:
                if isinstance(data['preferences'], str):
                    prefs = json.loads(data['preferences'])
                else:
                    prefs = data['preferences']
            except:
                prefs = {}
        
        return cls(
            pref_id=data.get('id'),
            odds_format=data.get('odds_format', 'american'),
            theme=data.get('theme', 'light'),
            notification_enabled=bool(data.get('notification_enabled', 1)),
            api_key=data.get('api_key'),
            preferences=prefs
        )
    
    def to_dict(self):
        """
        Convert UserPreferences object to dictionary.
        
        Returns:
            dict: Dictionary representation of the preferences
        """
        return {
            'id': self.id,
            'odds_format': self.odds_format,
            'theme': self.theme,
            'notification_enabled': 1 if self.notification_enabled else 0,
            'api_key': self.api_key,
            'preferences': json.dumps(self.preferences) if self.preferences else None
        }
