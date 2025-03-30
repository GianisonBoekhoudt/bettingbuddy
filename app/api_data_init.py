#!/usr/bin/env python3
"""
API Data Initialization Module for BettingBuddy app.

Fetches initial data from The Odds API and populates the database.
"""

import os
import sys
import requests
import json
from datetime import datetime

# Get API key from environment
API_KEY = os.getenv('THE_ODDS_API_KEY', '')

def init_database():
    """
    Initialize the database with data from The Odds API.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from database import BettingDatabase
        
        # Initialize database connection
        db = BettingDatabase()
        db.connect()
        
        # Get sports list from API
        print("Fetching sports data from API...")
        sports = fetch_sports()
        if not sports:
            print("Failed to fetch sports data. Check API key.")
            return False
        
        # Insert sports into database
        for sport in sports:
            # Check if sport already exists
            db.cursor.execute("SELECT id FROM sports WHERE api_id = ?", (sport['key'],))
            existing = db.cursor.fetchone()
            
            if existing:
                sport_id = existing['id']
                print(f"  Sport already exists: {sport['title']}")
            else:
                # Insert new sport
                db.cursor.execute(
                    "INSERT INTO sports (name, api_id, active) VALUES (?, ?, ?)",
                    (sport['title'], sport['key'], 1 if sport['active'] else 0)
                )
                sport_id = db.cursor.lastrowid
                print(f"  Added sport: {sport['title']}")
            
            # Get odds for this sport if it's active
            if sport['active']:
                print(f"  Fetching odds for {sport['title']}...")
                odds_data = fetch_odds(sport['key'])
                
                if odds_data:
                    # Process odds data and insert teams and bets
                    for event in odds_data:
                        try:
                            process_event(db, event, sport_id, sport['title'])
                        except Exception as e:
                            print(f"    Error processing event: {e}")
                else:
                    print(f"    No odds data available for {sport['title']}")
        
        # Commit all changes
        db.conn.commit()
        
        # Close the database connection
        db.close()
        
        print("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def fetch_sports():
    """
    Fetch sports data from The Odds API.
    
    Returns:
        list: List of sports or empty list on error
    """
    url = "https://api.the-odds-api.com/v4/sports"
    params = {
        "apiKey": API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error ({response.status_code}): {response.text}")
            return []
            
    except Exception as e:
        print(f"Error fetching sports: {e}")
        return []

def fetch_odds(sport_key, regions="us", markets="h2h"):
    """
    Fetch odds data for a specific sport.
    
    Args:
        sport_key (str): Sport key from the API
        regions (str, optional): Regions for the odds. Default is "us"
        markets (str, optional): Markets to fetch. Default is "h2h"
        
    Returns:
        list: List of events with odds or empty list on error
    """
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": regions,
        "markets": markets,
        "dateFormat": "iso"
    }
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error ({response.status_code}): {response.text}")
            return []
            
    except Exception as e:
        print(f"Error fetching odds: {e}")
        return []

def process_event(db, event, sport_id, sport_name):
    """
    Process event data and insert teams and bets.
    
    Args:
        db (BettingDatabase): Database connection
        event (dict): Event data from API
        sport_id (int): Sport ID in the database
        sport_name (str): Sport name
    """
    # Extract basic event info
    event_id = event.get("id")
    home_team = event.get("home_team")
    away_team = event.get("away_team")
    commence_time = event.get("commence_time")
    
    # Skip if missing critical data
    if not all([event_id, home_team, away_team, commence_time]):
        print(f"    Skipping event with missing data: {event_id}")
        return
    
    # Process bookmakers/odds
    bookmakers = event.get("bookmakers", [])
    if not bookmakers:
        print(f"    No bookmakers for event: {event_id}")
        return
    
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
        print(f"    No h2h market for event: {event_id}")
        return
    
    outcomes = h2h_market.get("outcomes", [])
    
    # Process teams and their odds
    for outcome in outcomes:
        team_name = outcome.get("name")
        if not team_name:
            continue
        
        odds = outcome.get("price")
        if not odds:
            continue
        
        # Format odds as American string
        if odds > 2.0:
            american_odds = f"+{int((odds - 1) * 100)}"
        else:
            american_odds = f"-{int(100 / (odds - 1))}"
        
        # Check if team exists, if not create it
        db.cursor.execute("SELECT id FROM teams WHERE name = ? AND sport_id = ?", (team_name, sport_id))
        team = db.cursor.fetchone()
        
        if team:
            team_id = team['id']
        else:
            db.cursor.execute(
                "INSERT INTO teams (name, sport_id, api_id) VALUES (?, ?, ?)",
                (team_name, sport_id, f"{event_id}_{team_name}")
            )
            team_id = db.cursor.lastrowid
        
        # Description for bet
        is_home = team_name == home_team
        opponent = away_team if is_home else home_team
        description = f"{team_name} vs {opponent}"
        
        # Check if bet already exists
        db.cursor.execute(
            "SELECT id FROM bets WHERE team_id = ? AND description = ? AND event_date = ?", 
            (team_id, description, commence_time)
        )
        bet = db.cursor.fetchone()
        
        if not bet:
            # Create new bet
            db.cursor.execute(
                """
                INSERT INTO bets (team_id, odds, description, event_date, status, 
                                commence_time, sport_name)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (team_id, american_odds, description, commence_time, commence_time, sport_name)
            )
