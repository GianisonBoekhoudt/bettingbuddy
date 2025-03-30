#!/usr/bin/env python3
"""
API Service module for BettingBuddy app.

Handles API requests to fetch odds data from external services.
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta

class APIService:
    """
    Service for interacting with external betting APIs.
    Primarily uses The Odds API for fetching odds data.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize the API service.
        
        Args:
            api_key (str, optional): API key for The Odds API. If None, tries to use from environment.
        """
        # Try to get API key from environment if not provided
        self.api_key = api_key or os.getenv('THE_ODDS_API_KEY', '')
        self.base_url = "https://api.the-odds-api.com"
        self.api_version = "v4"
        
        # Cache to store API responses
        self.cache = {}
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
    
    def set_api_key(self, api_key):
        """
        Set the API key.
        
        Args:
            api_key (str): API key for The Odds API
        """
        self.api_key = api_key
    
    def get_sports(self):
        """
        Get list of available sports from the API.
        
        Returns:
            list: List of sport dictionaries or empty list on error
        """
        endpoint = f"/{self.api_version}/sports"
        params = {
            "apiKey": self.api_key
        }
        
        # Check cache first
        cache_key = "sports"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            # If cache is still valid
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                return cache_entry["data"]
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store in cache
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": data
                }
                
                return data
            else:
                print(f"API error: {response.status_code}")
                print(response.text)
                return []
                
        except Exception as e:
            print(f"Error getting sports: {e}")
            return []
    
    def get_odds(self, sport_key, regions="us", markets="h2h", date_format="iso"):
        """
        Get odds for a specific sport.
        
        Args:
            sport_key (str): Sport key/ID from the API
            regions (str, optional): Regions for odds. Default is "us"
            markets (str, optional): Markets to fetch. Default is "h2h"
            date_format (str, optional): Date format for response. Default is "iso"
            
        Returns:
            list: List of odds dictionaries or empty list on error
        """
        endpoint = f"/{self.api_version}/sports/{sport_key}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "dateFormat": date_format
        }
        
        # Check cache first
        cache_key = f"odds_{sport_key}_{regions}_{markets}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            # If cache is still valid (shorter duration for odds)
            if time.time() - cache_entry["timestamp"] < (self.cache_duration / 2):
                return cache_entry["data"]
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store in cache
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": data
                }
                
                return data
            else:
                print(f"API error: {response.status_code}")
                print(response.text)
                return []
                
        except Exception as e:
            print(f"Error getting odds: {e}")
            return []
    
    def get_upcoming_events(self, sport_key=None, hours_ahead=48):
        """
        Get upcoming events for a specific sport or all sports.
        
        Args:
            sport_key (str, optional): Sport key/ID. If None, gets for all sports.
            hours_ahead (int, optional): Hours to look ahead. Default is 48.
            
        Returns:
            list: List of upcoming events
        """
        # If sport key is provided, get odds for that sport
        if sport_key:
            return self.get_odds(sport_key)
        
        # If no sport key, get all sports first
        sports = self.get_sports()
        
        all_events = []
        for sport in sports:
            # Skip sports that are not currently in season
            if not sport.get("active"):
                continue
                
            try:
                # Get odds for this sport
                odds = self.get_odds(sport["key"])
                
                # Filter by commence time if hours_ahead is specified
                if hours_ahead > 0:
                    now = datetime.now()
                    filtered_odds = []
                    
                    for event in odds:
                        commence_time_str = event.get("commence_time")
                        if commence_time_str:
                            try:
                                # Parse ISO format
                                commence_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
                                
                                # Only include events within the time window
                                if commence_time <= now + timedelta(hours=hours_ahead):
                                    filtered_odds.append(event)
                            except ValueError:
                                # If parsing fails, include the event anyway
                                filtered_odds.append(event)
                        else:
                            # No commence time, include it just in case
                            filtered_odds.append(event)
                    
                    all_events.extend(filtered_odds)
                else:
                    # No time filtering
                    all_events.extend(odds)
                    
            except Exception as e:
                print(f"Error getting odds for {sport['key']}: {e}")
        
        return all_events
    
    def process_odds_for_database(self, odds_data, sport_id, sport_name):
        """
        Process odds data from API into a format suitable for the database.
        
        Args:
            odds_data (list): Odds data from API
            sport_id (int): Sport ID in the database
            sport_name (str): Sport name
            
        Returns:
            tuple: (team_data, bet_data) for database insertion
        """
        team_data = []
        bet_data = []
        
        for event in odds_data:
            try:
                event_id = event.get("id")
                home_team = event.get("home_team")
                away_team = event.get("away_team")
                commence_time = event.get("commence_time")
                
                # Process bookmakers/odds
                bookmakers = event.get("bookmakers", [])
                if not bookmakers:
                    continue
                
                # Use the first bookmaker for simplicity
                bookmaker = bookmakers[0]
                markets = bookmaker.get("markets", [])
                
                # Find head-to-head (moneyline) market
                h2h_market = None
                for market in markets:
                    if market.get("key") == "h2h":
                        h2h_market = market
                        break
                
                if not h2h_market:
                    continue
                
                outcomes = h2h_market.get("outcomes", [])
                
                # Add teams and their odds
                for outcome in outcomes:
                    team_name = outcome.get("name")
                    if not team_name:
                        continue
                    
                    odds = outcome.get("price")
                    if not odds:
                        continue
                    
                    # Format odds as American string
                    odds_str = str(odds)
                    if odds > 2.0:
                        american_odds = f"+{int((odds - 1) * 100)}"
                    else:
                        american_odds = f"-{int(100 / (odds - 1))}"
                    
                    # Add team data
                    team_data.append({
                        "name": team_name,
                        "sport_id": sport_id,
                        "api_id": f"{event_id}_{team_name}"
                    })
                    
                    # Description for bet
                    is_home = team_name == home_team
                    opponent = away_team if is_home else home_team
                    description = f"{team_name} vs {opponent}"
                    
                    # Add bet data
                    bet_data.append({
                        "team_name": team_name,
                        "odds": american_odds,
                        "description": description,
                        "event_date": commence_time,
                        "commence_time": commence_time,
                        "sport_name": sport_name
                    })
            
            except Exception as e:
                print(f"Error processing event: {e}")
                continue
        
        return (team_data, bet_data)
