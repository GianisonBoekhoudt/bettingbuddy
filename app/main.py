#!/usr/bin/env python3
"""
BettingBuddy - Sports Betting Analysis and Parlay Recommender

Main application entry point for the BettingBuddy Kivy app.
This app helps users track betting opportunities and provides
parlay recommendations based on odds analysis.
"""

import os
import sys
import json
from datetime import datetime

# Kivy imports
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, ObjectProperty, NumericProperty

# Local module imports
from database import BettingDatabase
from models import Sport, Team, Bet, Parlay, UserPreferences
from parlay_recommendations import ParlayRecommender
from api_service import APIService
from api_data_init import init_database

# Import UI screens
from ui.screens import LoadingScreen, AboutScreen, ErrorScreen
from ui.homescreen import HomeScreen  
from ui.betscreen import BetScreen, BetDetailScreen
from ui.parlayscreen import ParlayScreen, ParlayDetailScreen
from ui.settingsscreen import SettingsScreen


class BettingBuddyApp(App):
    """
    Main application class for BettingBuddy.
    """
    # App theme properties
    primary_color = ListProperty([0.129, 0.588, 0.953, 1])  # #2196F3
    accent_color = ListProperty([1, 0.596, 0, 1])          # #FF9800
    background_color = ListProperty([0.95, 0.95, 0.95, 1])  # Light gray
    dark_primary_color = ListProperty([0.067, 0.384, 0.671, 1])  # Darker blue
    
    # Current user settings and state
    odds_format = StringProperty('american')  # 'american', 'decimal', 'fractional'
    current_sport_filter = StringProperty('all')
    
    # Database connection
    db = ObjectProperty(None)
    api_service = ObjectProperty(None)
    parlay_recommender = ObjectProperty(None)
    
    def build(self):
        """
        Build the application UI.
        """
        # Set app title that appears in the window title
        self.title = 'BettingBuddy'
        
        # Load main KV file
        Builder.load_file(os.path.join(os.path.dirname(__file__), 'bettingbuddy.kv'))
        
        # Create screen manager
        self.sm = ScreenManager(transition=SlideTransition())
        
        # Add loading screen first
        self.loading_screen = LoadingScreen(name='loading')
        self.sm.add_widget(self.loading_screen)
        
        # Schedule the initialization to occur after the loading screen is displayed
        Clock.schedule_once(self.initialize_app, 0.5)
        
        return self.sm
    
    def initialize_app(self, dt):
        """Initialize the app components and database."""
        try:
            # Initialize database connection
            self.db = BettingDatabase()
            self.db.connect()
            
            # Initialize API Service
            self.api_service = APIService()
            
            # Initialize parlay recommender
            self.parlay_recommender = ParlayRecommender()
            
            # Check if database has data, if not initialize
            self.db.cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='sports'")
            has_tables = self.db.cursor.fetchone()[0] > 0
            
            if has_tables:
                # Check if there are any sports
                self.db.cursor.execute("SELECT COUNT(*) FROM sports")
                has_sports = self.db.cursor.fetchone()[0] > 0
                
                if not has_sports:
                    # Need to populate database
                    self.loading_screen.update_status("Initializing database with sports data...")
                    success = init_database()
                    if not success:
                        self.show_error("Failed to initialize database. Please check API key.")
                        return
            else:
                # Create database structure and initialize
                self.loading_screen.update_status("Creating database schema...")
                self._create_database_schema()
                
                self.loading_screen.update_status("Initializing database with sports data...")
                success = init_database()
                if not success:
                    self.show_error("Failed to initialize database. Please check API key.")
                    return
            
            # Load user preferences
            self._load_user_preferences()
            
            # Add all screens
            self.home_screen = HomeScreen(name='home')
            self.bet_screen = BetScreen(name='bets')
            self.bet_detail_screen = BetDetailScreen(name='bet_detail')
            self.parlay_screen = ParlayScreen(name='parlays')
            self.parlay_detail_screen = ParlayDetailScreen(name='parlay_detail')
            self.settings_screen = SettingsScreen(name='settings')
            self.about_screen = AboutScreen(name='about')
            
            self.sm.add_widget(self.home_screen)
            self.sm.add_widget(self.bet_screen)
            self.sm.add_widget(self.bet_detail_screen)
            self.sm.add_widget(self.parlay_screen)
            self.sm.add_widget(self.parlay_detail_screen)
            self.sm.add_widget(self.settings_screen)
            self.sm.add_widget(self.about_screen)
            
            # Switch to home screen
            self.sm.current = 'home'
            
        except Exception as e:
            self.show_error(f"Error initializing app: {str(e)}")
    
    def _create_database_schema(self):
        """Create the database schema if it doesn't exist."""
        # Create Sports table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS sports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            api_id TEXT,
            active INTEGER DEFAULT 1,
            icon_path TEXT
        )
        ''')
        
        # Create Teams table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sport_id INTEGER NOT NULL,
            api_id TEXT,
            logo_path TEXT,
            FOREIGN KEY (sport_id) REFERENCES sports(id)
        )
        ''')
        
        # Create Bets table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            odds TEXT NOT NULL,
            description TEXT,
            event_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            result TEXT,
            active INTEGER DEFAULT 1,
            commence_time TEXT,
            sport_name TEXT,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
        ''')
        
        # Create Parlays table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS parlays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stake REAL NOT NULL,
            total_odds TEXT NOT NULL,
            potential_payout REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            notes TEXT
        )
        ''')
        
        # Create Parlay_Bets junction table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS parlay_bets (
            parlay_id INTEGER,
            bet_id INTEGER,
            PRIMARY KEY (parlay_id, bet_id),
            FOREIGN KEY (parlay_id) REFERENCES parlays(id),
            FOREIGN KEY (bet_id) REFERENCES bets(id)
        )
        ''')
        
        # Create User_Preferences table
        self.db.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            odds_format TEXT DEFAULT 'american',
            theme TEXT DEFAULT 'light',
            notification_enabled INTEGER DEFAULT 1,
            api_key TEXT,
            preferences TEXT
        )
        ''')
        
        # Commit the changes
        self.db.conn.commit()
    
    def _load_user_preferences(self):
        """Load user preferences from the database."""
        try:
            # Check if we have user preferences
            self.db.cursor.execute("SELECT COUNT(*) FROM user_preferences")
            has_preferences = self.db.cursor.fetchone()[0] > 0
            
            if has_preferences:
                # Load existing preferences
                self.db.cursor.execute("SELECT * FROM user_preferences ORDER BY id DESC LIMIT 1")
                prefs = dict(self.db.cursor.fetchone())
                
                # Set odds format
                if prefs.get('odds_format'):
                    self.odds_format = prefs['odds_format']
                
                # Set theme if available
                theme = prefs.get('theme', 'light')
                # Would apply theme here if we had theme support
            else:
                # Create default preferences
                self.db.cursor.execute(
                    "INSERT INTO user_preferences (odds_format, theme, notification_enabled) VALUES (?, ?, ?)",
                    ('american', 'light', 1)
                )
                self.db.conn.commit()
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def show_error(self, message):
        """Show an error screen with the given message."""
        error_screen = ErrorScreen(name='error')
        error_screen.error_message = message
        self.sm.add_widget(error_screen)
        self.sm.current = 'error'
    
    def show_loading(self, message="Loading..."):
        """Show loading screen with custom message."""
        if 'loading' not in self.sm.screen_names:
            self.sm.add_widget(LoadingScreen(name='loading'))
        
        loading_screen = self.sm.get_screen('loading')
        loading_screen.loading_message = message
        self.sm.current = 'loading'
    
    def convert_odds(self, odds_str, target_format=None):
        """
        Convert odds between different formats.
        
        Args:
            odds_str (str): The odds string to convert
            target_format (str, optional): Target format. If None, uses app's current format
            
        Returns:
            str: Converted odds string
        """
        if target_format is None:
            target_format = self.odds_format
        
        try:
            # Parse the input odds
            odds_float = 0
            
            # Try to determine the input format
            if odds_str.startswith('+') or odds_str.startswith('-'):
                # American format
                american_odds = int(odds_str)
                if american_odds > 0:
                    odds_float = american_odds / 100
                else:
                    odds_float = 100 / abs(american_odds)
                
                # Add 1 to get decimal odds
                odds_decimal = odds_float + 1
            elif '/' in odds_str:
                # Fractional format (e.g., "5/1")
                num, denom = odds_str.split('/')
                odds_float = float(num) / float(denom)
                odds_decimal = odds_float + 1
            else:
                # Assume decimal format
                odds_decimal = float(odds_str)
            
            # Convert to the target format
            if target_format == 'american':
                if odds_decimal >= 2.0:
                    return f"+{int((odds_decimal - 1) * 100)}"
                else:
                    return f"-{int(100 / (odds_decimal - 1))}"
            elif target_format == 'decimal':
                return f"{odds_decimal:.2f}"
            elif target_format == 'fractional':
                # Convert decimal odds to fractional (simplified)
                decimal_minus_one = odds_decimal - 1
                if decimal_minus_one.is_integer():
                    return f"{int(decimal_minus_one)}/1"
                
                # Try common fractions
                if abs(decimal_minus_one - 0.5) < 0.01:
                    return "1/2"
                elif abs(decimal_minus_one - 1.5) < 0.01:
                    return "3/2"
                elif abs(decimal_minus_one - 0.33) < 0.01:
                    return "1/3"
                else:
                    # Fallback to approximation
                    return f"{decimal_minus_one:.2f}/1"
                
        except Exception as e:
            print(f"Error converting odds: {e}")
            return odds_str
    
    def on_stop(self):
        """Clean up resources when the app is closed."""
        if self.db:
            self.db.close()


if __name__ == '__main__':
    BettingBuddyApp().run()
