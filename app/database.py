#!/usr/bin/env python3
"""
Database module for BettingBuddy app.

Handles database connections, queries, and CRUD operations
for the app's SQLite database.
"""

import os
import sqlite3
from datetime import datetime

class BettingDatabase:
    """
    Database handler for the BettingBuddy app.
    Manages connections and operations for the SQLite database.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the database connection.
        
        Args:
            db_path (str, optional): Path to the database file. If None, uses default path.
        """
        if db_path is None:
            # Use default path in the app directory or one level up if running from app/
            app_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(app_dir)
            
            if os.path.basename(app_dir) == 'app':
                # We're in the app directory, store DB one level up
                self.db_path = os.path.join(parent_dir, 'bettingbuddy.db')
            else:
                # We're already at the root, store DB here
                self.db_path = os.path.join(app_dir, 'bettingbuddy.db')
        else:
            self.db_path = db_path
        
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """
        Establish a connection to the SQLite database.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            # Use Row factory for dictionary-like access
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def commit(self):
        """
        Commit the current transaction.
        """
        if self.conn:
            self.conn.commit()
    
    def execute(self, query, params=None):
        """
        Execute a SQL query with optional parameters.
        
        Args:
            query (str): SQL query to execute
            params (tuple, optional): Parameters for the query
            
        Returns:
            sqlite3.Cursor: Query cursor
        """
        try:
            if params:
                return self.cursor.execute(query, params)
            else:
                return self.cursor.execute(query)
        except sqlite3.Error as e:
            print(f"Query execution error: {e}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            return None
    
    def fetchone(self):
        """
        Fetch a single row from the last query.
        
        Returns:
            dict or None: Row as a dictionary or None if no results
        """
        if self.cursor:
            row = self.cursor.fetchone()
            return dict(row) if row else None
        return None
    
    def fetchall(self):
        """
        Fetch all rows from the last query.
        
        Returns:
            list: List of dictionaries representing rows
        """
        if self.cursor:
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        return []
    
    # CRUD operations for Sports
    def create_sport(self, name, api_id=None, active=1, icon_path=None):
        """
        Create a new sport record.
        
        Args:
            name (str): Sport name
            api_id (str, optional): API identifier for the sport
            active (int, optional): 1 if active, 0 otherwise
            icon_path (str, optional): Path to the sport's icon
            
        Returns:
            int: ID of the new sport or None if error
        """
        try:
            self.execute(
                "INSERT INTO sports (name, api_id, active, icon_path) VALUES (?, ?, ?, ?)",
                (name, api_id, active, icon_path)
            )
            self.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error creating sport: {e}")
            return None
    
    def get_sports(self, active_only=True):
        """
        Get list of sports.
        
        Args:
            active_only (bool, optional): If True, return only active sports
            
        Returns:
            list: List of sport dictionaries
        """
        if active_only:
            self.execute("SELECT * FROM sports WHERE active = 1 ORDER BY name")
        else:
            self.execute("SELECT * FROM sports ORDER BY name")
        return self.fetchall()
    
    def get_sport_by_id(self, sport_id):
        """
        Get sport by ID.
        
        Args:
            sport_id (int): Sport ID
            
        Returns:
            dict or None: Sport data or None if not found
        """
        self.execute("SELECT * FROM sports WHERE id = ?", (sport_id,))
        return self.fetchone()
    
    def get_sport_by_api_id(self, api_id):
        """
        Get sport by API ID.
        
        Args:
            api_id (str): Sport API ID
            
        Returns:
            dict or None: Sport data or None if not found
        """
        self.execute("SELECT * FROM sports WHERE api_id = ?", (api_id,))
        return self.fetchone()
    
    # CRUD operations for Teams
    def create_team(self, name, sport_id, api_id=None, logo_path=None):
        """
        Create a new team record.
        
        Args:
            name (str): Team name
            sport_id (int): Sport ID this team belongs to
            api_id (str, optional): API identifier for the team
            logo_path (str, optional): Path to the team's logo
            
        Returns:
            int: ID of the new team or None if error
        """
        try:
            self.execute(
                "INSERT INTO teams (name, sport_id, api_id, logo_path) VALUES (?, ?, ?, ?)",
                (name, sport_id, api_id, logo_path)
            )
            self.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error creating team: {e}")
            return None
    
    def get_teams_by_sport(self, sport_id):
        """
        Get teams for a specific sport.
        
        Args:
            sport_id (int): Sport ID
            
        Returns:
            list: List of team dictionaries
        """
        self.execute("SELECT * FROM teams WHERE sport_id = ? ORDER BY name", (sport_id,))
        return self.fetchall()
    
    def get_team_by_id(self, team_id):
        """
        Get team by ID.
        
        Args:
            team_id (int): Team ID
            
        Returns:
            dict or None: Team data or None if not found
        """
        self.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        return self.fetchone()
    
    def get_team_by_api_id(self, api_id):
        """
        Get team by API ID.
        
        Args:
            api_id (str): Team API ID
            
        Returns:
            dict or None: Team data or None if not found
        """
        self.execute("SELECT * FROM teams WHERE api_id = ?", (api_id,))
        return self.fetchone()
    
    # CRUD operations for Bets
    def create_bet(self, team_id, odds, description=None, event_date=None, status="pending", 
                  result=None, active=1, commence_time=None, sport_name=None):
        """
        Create a new bet record.
        
        Args:
            team_id (int): Team ID this bet is for
            odds (str): Betting odds
            description (str, optional): Bet description
            event_date (str, optional): Event date/time
            status (str, optional): Bet status (pending, won, lost)
            result (str, optional): Bet result
            active (int, optional): 1 if active, 0 otherwise
            commence_time (str, optional): Event start time
            sport_name (str, optional): Sport name
            
        Returns:
            int: ID of the new bet or None if error
        """
        try:
            self.execute(
                """
                INSERT INTO bets (team_id, odds, description, event_date, status, 
                                 result, active, commence_time, sport_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (team_id, odds, description, event_date, status, result, active, commence_time, sport_name)
            )
            self.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error creating bet: {e}")
            return None
    
    def get_bet_by_id(self, bet_id):
        """
        Get bet by ID.
        
        Args:
            bet_id (int): Bet ID
            
        Returns:
            dict or None: Bet data or None if not found
        """
        self.execute(
            """
            SELECT b.*, t.name as team_name, s.name as sport_name 
            FROM bets b 
            JOIN teams t ON b.team_id = t.id 
            JOIN sports s ON t.sport_id = s.id 
            WHERE b.id = ?
            """, 
            (bet_id,)
        )
        return self.fetchone()
    
    def get_active_bets(self, sport_id=None):
        """
        Get active bets, optionally filtered by sport.
        
        Args:
            sport_id (int, optional): Sport ID to filter by
            
        Returns:
            list: List of bet dictionaries
        """
        if sport_id:
            self.execute(
                """
                SELECT b.*, t.name as team_name, s.name as sport_name 
                FROM bets b 
                JOIN teams t ON b.team_id = t.id 
                JOIN sports s ON t.sport_id = s.id 
                WHERE b.active = 1 AND t.sport_id = ? 
                ORDER BY b.event_date
                """, 
                (sport_id,)
            )
        else:
            self.execute(
                """
                SELECT b.*, t.name as team_name, s.name as sport_name 
                FROM bets b 
                JOIN teams t ON b.team_id = t.id 
                JOIN sports s ON t.sport_id = s.id 
                WHERE b.active = 1 
                ORDER BY b.event_date
                """
            )
        return self.fetchall()
    
    def update_bet_status(self, bet_id, status, result=None):
        """
        Update bet status and result.
        
        Args:
            bet_id (int): Bet ID
            status (str): New status (pending, won, lost)
            result (str, optional): Bet result
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.execute(
                "UPDATE bets SET status = ?, result = ? WHERE id = ?",
                (status, result, bet_id)
            )
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating bet status: {e}")
            return False
    
    # CRUD operations for Parlays
    def create_parlay(self, bet_ids, stake, total_odds, potential_payout, notes=None):
        """
        Create a new parlay with associated bets.
        
        Args:
            bet_ids (list): List of bet IDs to include in parlay
            stake (float): Stake amount
            total_odds (str): Total parlay odds
            potential_payout (float): Potential payout
            notes (str, optional): Parlay notes
            
        Returns:
            int: ID of the new parlay or None if error
        """
        try:
            # Start a transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Create parlay
            self.execute(
                """
                INSERT INTO parlays (stake, total_odds, potential_payout, notes, created_at, status)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'pending')
                """,
                (stake, total_odds, potential_payout, notes)
            )
            parlay_id = self.cursor.lastrowid
            
            # Add bets to parlay
            for bet_id in bet_ids:
                self.execute(
                    "INSERT INTO parlay_bets (parlay_id, bet_id) VALUES (?, ?)",
                    (parlay_id, bet_id)
                )
            
            # Commit transaction
            self.conn.commit()
            return parlay_id
        except Exception as e:
            # Rollback in case of error
            self.conn.rollback()
            print(f"Error creating parlay: {e}")
            return None
    
    def get_parlay_by_id(self, parlay_id):
        """
        Get parlay and its bets by ID.
        
        Args:
            parlay_id (int): Parlay ID
            
        Returns:
            dict: Parlay data with bets
        """
        # Get parlay
        self.execute("SELECT * FROM parlays WHERE id = ?", (parlay_id,))
        parlay = self.fetchone()
        
        if not parlay:
            return None
        
        # Get associated bets
        self.execute(
            """
            SELECT b.*, t.name as team_name, s.name as sport_name
            FROM bets b
            JOIN parlay_bets pb ON b.id = pb.bet_id
            JOIN teams t ON b.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE pb.parlay_id = ?
            """,
            (parlay_id,)
        )
        bets = self.fetchall()
        
        # Add bets to parlay dict
        parlay['bets'] = bets
        
        return parlay
    
    def get_all_parlays(self):
        """
        Get all parlays with their summary info.
        
        Returns:
            list: List of parlay dictionaries
        """
        self.execute(
            """
            SELECT p.*, COUNT(pb.bet_id) as bet_count
            FROM parlays p
            LEFT JOIN parlay_bets pb ON p.id = pb.parlay_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            """
        )
        return self.fetchall()
    
    def update_parlay_status(self, parlay_id, status):
        """
        Update parlay status.
        
        Args:
            parlay_id (int): Parlay ID
            status (str): New status (pending, won, lost)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.execute(
                "UPDATE parlays SET status = ? WHERE id = ?",
                (status, parlay_id)
            )
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating parlay status: {e}")
            return False
    
    # User preferences
    def get_user_preferences(self):
        """
        Get user preferences.
        
        Returns:
            dict: User preferences
        """
        self.execute("SELECT * FROM user_preferences ORDER BY id DESC LIMIT 1")
        return self.fetchone()
    
    def update_user_preferences(self, odds_format=None, theme=None, notification_enabled=None, api_key=None):
        """
        Update user preferences.
        
        Args:
            odds_format (str, optional): Odds format preference
            theme (str, optional): Theme preference
            notification_enabled (int, optional): Notification preference
            api_key (str, optional): API key
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current preferences
            current = self.get_user_preferences()
            
            # Prepare update values
            new_odds_format = odds_format if odds_format is not None else current.get('odds_format')
            new_theme = theme if theme is not None else current.get('theme')
            new_notification = notification_enabled if notification_enabled is not None else current.get('notification_enabled')
            new_api_key = api_key if api_key is not None else current.get('api_key')
            
            self.execute(
                """
                UPDATE user_preferences 
                SET odds_format = ?, theme = ?, notification_enabled = ?, api_key = ?
                WHERE id = ?
                """,
                (new_odds_format, new_theme, new_notification, new_api_key, current['id'])
            )
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False
