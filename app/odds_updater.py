"""
BettingBuddy Odds Updater

This module handles updating odds for existing bets and parlays.
"""

import threading
import time
from typing import Dict, List, Callable, Optional, Any
import datetime

from models import Bet, Parlay, Team, Sport, UserPreferences
from database import BettingDatabase, calculate_parlay_odds, calculate_payout
from api_service import APIService

class OddsUpdateManager:
    """Manager for updating odds in the app."""
    
    def __init__(self, db=None, api_service=None):
        """
        Initialize the OddsUpdateManager.
        
        Args:
            db (BettingDatabase, optional): The database instance
            api_service (APIService, optional): The API service instance
        """
        self.db = db or BettingDatabase()
        self.api_service = api_service or APIService()
        
        # Load user settings
        self._load_settings()
        
        # Thread for automatic updates
        self.update_thread = None
        self.stop_thread = False
        
        # Callbacks to call after updates
        self.callbacks = {}
        
        # Keep track of when each sport was last updated
        self.last_sport_update = {}
    
    def _load_settings(self):
        """Load settings from user preferences."""
        prefs = UserPreferences.get()
        
        # Get API key
        if prefs.api_key:
            self.api_service.set_api_key(prefs.api_key)
        
        # Get update settings
        self.auto_update = prefs.preferences.get('auto_update_odds', True)
        self.update_interval = prefs.preferences.get('odds_update_interval', 3600)  # Default to 1 hour
        
        # Set sport-specific update limits (in seconds)
        self.sport_update_limits = {
            # These are minimums to avoid too frequent updates
            'basketball_nba': 1800,  # 30 minutes for NBA
            'americanfootball_nfl': 3600,  # 1 hour for NFL
            'baseball_mlb': 1800,  # 30 minutes for MLB
            'mma_mixed_martial_arts': 7200,  # 2 hours for MMA
            'icehockey_nhl': 1800,  # 30 minutes for NHL
            # Default for other sports
            'default': 3600  # 1 hour
        }
    
    def set_api_key(self, api_key):
        """Set the API key for the odds service."""
        self.api_service.set_api_key(api_key)
    
    def register_callback(self, callback_id: str, callback_func: Callable):
        """
        Register a callback function to be called when odds are updated.
        
        Args:
            callback_id (str): A unique identifier for the callback
            callback_func (Callable): The function to call after odds are updated
        """
        self.callbacks[callback_id] = callback_func
    
    def unregister_callback(self, callback_id: str):
        """
        Unregister a callback function.
        
        Args:
            callback_id (str): The callback identifier to remove
        """
        if callback_id in self.callbacks:
            del self.callbacks[callback_id]
    
    def start_updates(self, interval=None):
        """
        Start the odds update thread.
        
        Args:
            interval (int, optional): Update interval in seconds
        """
        # If already running, stop it first
        if self.update_thread and self.update_thread.is_alive():
            self.stop_updates()
        
        # Set interval if provided
        if interval is not None:
            self.update_interval = interval
        
        # Create a new thread
        self.stop_thread = False
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        print(f"Started odds update thread with interval {self.update_interval} seconds")
    
    def stop_updates(self):
        """Stop the odds update thread."""
        if self.update_thread and self.update_thread.is_alive():
            self.stop_thread = True
            self.update_thread.join(timeout=2.0)
            print("Stopped odds update thread")
    
    def update_now(self):
        """Force an immediate update of all odds."""
        # Update all odds directly in the current thread
        self._update_all_odds()
        
        # Trigger callbacks
        for callback in self.callbacks.values():
            try:
                callback()
            except Exception as e:
                print(f"Error in update callback: {e}")
    
    def _update_loop(self):
        """Main update loop that runs in a separate thread."""
        while not self.stop_thread:
            try:
                # Update all odds
                self._update_all_odds()
                
                # Trigger callbacks
                for callback in self.callbacks.values():
                    try:
                        callback()
                    except Exception as e:
                        print(f"Error in update callback: {e}")
                
                # Sleep until next update
                for _ in range(int(self.update_interval)):
                    if self.stop_thread:
                        break
                    time.sleep(1)
            except Exception as e:
                print(f"Error in odds update loop: {e}")
                time.sleep(60)  # Sleep for 1 minute on error
    
    def _update_all_odds(self):
        """Update odds for all active bets."""
        try:
            # Make sure we have an API key
            if not self.api_service.api_key:
                print("No API key set, skipping odds update")
                return
            
            # Get all active bets that need updating
            bets = Bet.get_active_bets()
            if not bets:
                print("No active bets to update")
                return
            
            print(f"Updating odds for {len(bets)} active bets")
            
            # Group bets by sport to minimize API calls
            sport_bets = self._group_bets_by_sport(bets)
            
            # Update odds for each sport
            for sport_id, sport_bets in sport_bets.items():
                try:
                    # Get the sport API ID
                    sport = Sport.get_by_id(sport_id)
                    if not sport or not sport.api_id:
                        print(f"Sport ID {sport_id} not found or has no API ID")
                        continue
                    
                    # Check if we should update this sport yet
                    if not self._should_update_sport(sport.api_id):
                        print(f"Skipping odds update for {sport.name} (updated recently)")
                        continue
                    
                    print(f"Updating odds for sport: {sport.name} ({sport.api_id})")
                    
                    # Get odds data from API
                    odds_data = self.api_service.get_odds(sport.api_id)
                    if not odds_data:
                        print(f"No odds data received for {sport.name}")
                        continue
                    
                    # Update each bet's odds
                    for bet in sport_bets:
                        team_name = bet.team_name
                        if not team_name:
                            # Try to get team name from ID
                            if bet.team_id:
                                team = Team.get_by_id(bet.team_id)
                                if team:
                                    team_name = team.name
                        
                        if not team_name:
                            print(f"Bet ID {bet.id} has no team name")
                            continue
                        
                        # Find the latest odds for this team
                        new_odds = self._find_team_odds(odds_data, team_name)
                        if new_odds:
                            print(f"Found new odds for {team_name}: {new_odds}")
                            self._update_bet_odds(bet, new_odds)
                        else:
                            print(f"No new odds found for {team_name}")
                    
                    # Mark this sport as updated
                    self.last_sport_update[sport.api_id] = time.time()
                    
                except Exception as e:
                    print(f"Error updating odds for sport ID {sport_id}: {e}")
            
            # Update parlays with the new bet odds
            self._update_parlays()
            
        except Exception as e:
            print(f"Error in _update_all_odds: {e}")
    
    def _should_update_sport(self, sport_api_id):
        """
        Check if we should update a sport based on last update time.
        
        Args:
            sport_api_id (str): The sport API ID
            
        Returns:
            bool: True if the sport should be updated, False otherwise
        """
        # If never updated, update now
        if sport_api_id not in self.last_sport_update:
            return True
        
        # Get the minimum time between updates for this sport
        min_update_time = self.sport_update_limits.get(
            sport_api_id, self.sport_update_limits['default']
        )
        
        # Check if enough time has passed
        time_since_update = time.time() - self.last_sport_update[sport_api_id]
        return time_since_update >= min_update_time
    
    def _group_bets_by_sport(self, bets):
        """
        Group bets by sport name and find the corresponding sport ID.
        
        Args:
            bets (List[Bet]): List of bets to group
            
        Returns:
            Dict[int, List[Bet]]: Dictionary mapping sport ID to list of bets
        """
        # First group by sport name
        by_sport_name = {}
        for bet in bets:
            sport_name = bet.sport_name
            if not sport_name:
                continue
            
            if sport_name not in by_sport_name:
                by_sport_name[sport_name] = []
            by_sport_name[sport_name].append(bet)
        
        # Then map to sport IDs
        grouped = {}
        all_sports = Sport.get_all_active()
        sport_id_map = {sport.name: sport.id for sport in all_sports}
        
        for sport_name, sport_bets in by_sport_name.items():
            # Find sport ID by name
            sport_id = sport_id_map.get(sport_name)
            if sport_id:
                grouped[sport_id] = sport_bets
            else:
                print(f"Warning: No sport ID found for sport {sport_name}")
                
        return grouped
    
    def _find_team_odds(self, odds_data, team_name):
        """
        Find the latest odds for a team from the odds data.
        
        Args:
            odds_data (List[Dict]): List of events with odds data
            team_name (str): The team name to search for
            
        Returns:
            str: The latest odds for the team, or None if not found
        """
        for event in odds_data:
            # Check if team is in this event
            if (team_name.lower() in event.get('home_team', '').lower() or 
                team_name.lower() in event.get('away_team', '').lower()):
                
                # Extract odds
                if 'bookmakers' in event and event['bookmakers']:
                    # Use first bookmaker
                    bookmaker = event['bookmakers'][0]
                    
                    # Look for h2h market
                    h2h_market = next((m for m in bookmaker.get('markets', []) 
                                      if m.get('key') == 'h2h'), None)
                    
                    if h2h_market and 'outcomes' in h2h_market:
                        # Find the team
                        team_outcome = next((o for o in h2h_market['outcomes'] 
                                           if team_name.lower() in o.get('name', '').lower()), None)
                        
                        if team_outcome and 'price' in team_outcome:
                            price = team_outcome['price']
                            # Format odds
                            return f"+{price}" if price > 0 else f"{price}"
        
        return None
    
    def _update_bet_odds(self, bet, new_odds):
        """
        Update a bet with new odds.
        
        Args:
            bet (Bet): The bet to update
            new_odds (str): The new odds value
        """
        # Store the previous odds
        previous_odds = bet.odds
        
        # Only update if odds have changed
        if previous_odds != new_odds:
            print(f"Updating bet {bet.id} odds from {previous_odds} to {new_odds}")
            
            # Update the bet object with new odds
            # Note: We don't track previous odds or last update time in the Bet model
            # but we print it for debugging purposes
            bet.odds = new_odds
            
            # Save to database
            bet.save()
    
    def _update_parlays(self):
        """Update all parlays after bets have been updated."""
        try:
            # Get all active parlays
            parlays = Parlay.get_all(status='active')
            if not parlays:
                print("No active parlays to update")
                return
            
            print(f"Updating {len(parlays)} active parlays")
            
            for parlay in parlays:
                # Calculate new total odds based on updated bet odds
                new_total_odds = calculate_parlay_odds([bet.odds for bet in parlay.bets])
                
                # Calculate new potential payout
                new_payout = calculate_payout(new_total_odds, parlay.stake)
                
                # Only update if values have changed
                if parlay.total_odds != new_total_odds or parlay.potential_payout != new_payout:
                    print(f"Updating parlay {parlay.id} odds from {parlay.total_odds} to {new_total_odds}")
                    
                    # Update the parlay
                    parlay.total_odds = new_total_odds
                    parlay.potential_payout = new_payout
                    parlay.save()
        
        except Exception as e:
            print(f"Error updating parlays: {e}")