#!/usr/bin/env python3
"""
Settings Screen Module for BettingBuddy app.

Implements the settings and preferences screen.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock

import os
import json

from ui.screens import HeaderBar, NavigationBar


class SettingsScreen(Screen):
    """Screen for app settings and preferences."""
    
    api_key = StringProperty("")
    notifications_enabled = BooleanProperty(True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(title="Settings")
        self.layout.add_widget(self.header)
        
        # Settings content
        self.content = GridLayout(
            cols=1,
            spacing=dp(20),
            padding=[dp(15), dp(15)],
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        
        # API Key section
        self.api_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            spacing=dp(10)
        )
        
        self.api_header = Label(
            text="API Settings",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            halign="left",
            text_size=(dp(500), dp(30))
        )
        
        self.api_description = Label(
            text="Enter your API key for The Odds API to get live odds data. Get a free key at https://the-odds-api.com",
            size_hint_y=None,
            height=dp(40),
            halign="left",
            text_size=(dp(500), dp(40))
        )
        
        self.api_input_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        self.api_input = TextInput(
            hint_text="Enter API key",
            multiline=False,
            password=True,
            size_hint_x=0.7
        )
        
        self.api_save_btn = Button(
            text="Save Key",
            size_hint_x=0.3
        )
        self.api_save_btn.bind(on_release=self.save_api_key)
        
        self.api_input_row.add_widget(self.api_input)
        self.api_input_row.add_widget(self.api_save_btn)
        
        self.api_section.add_widget(self.api_header)
        self.api_section.add_widget(self.api_description)
        self.api_section.add_widget(self.api_input_row)
        
        # Display preferences section
        self.display_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(150),
            spacing=dp(10)
        )
        
        self.display_header = Label(
            text="Display Settings",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            halign="left",
            text_size=(dp(500), dp(30))
        )
        
        # Odds format row
        self.odds_row = BoxLayout(
            orientation="horizontal", 
            size_hint_y=None,
            height=dp(40)
        )
        
        self.odds_label = Label(
            text="Odds Format:",
            size_hint_x=0.4,
            halign="left",
            text_size=(dp(200), dp(40))
        )
        
        self.odds_american_btn = Button(
            text="American",
            size_hint_x=0.2
        )
        self.odds_american_btn.bind(on_release=lambda x: self.set_odds_format("american"))
        
        self.odds_decimal_btn = Button(
            text="Decimal",
            size_hint_x=0.2
        )
        self.odds_decimal_btn.bind(on_release=lambda x: self.set_odds_format("decimal"))
        
        self.odds_fractional_btn = Button(
            text="Fractional",
            size_hint_x=0.2
        )
        self.odds_fractional_btn.bind(on_release=lambda x: self.set_odds_format("fractional"))
        
        self.odds_row.add_widget(self.odds_label)
        self.odds_row.add_widget(self.odds_american_btn)
        self.odds_row.add_widget(self.odds_decimal_btn)
        self.odds_row.add_widget(self.odds_fractional_btn)
        
        # Theme row
        self.theme_row = BoxLayout(
            orientation="horizontal", 
            size_hint_y=None,
            height=dp(40)
        )
        
        self.theme_label = Label(
            text="Theme:",
            size_hint_x=0.4,
            halign="left",
            text_size=(dp(200), dp(40))
        )
        
        self.theme_light_btn = Button(
            text="Light",
            size_hint_x=0.3
        )
        self.theme_light_btn.bind(on_release=lambda x: self.set_theme("light"))
        
        self.theme_dark_btn = Button(
            text="Dark",
            size_hint_x=0.3
        )
        self.theme_dark_btn.bind(on_release=lambda x: self.set_theme("dark"))
        
        self.theme_row.add_widget(self.theme_label)
        self.theme_row.add_widget(self.theme_light_btn)
        self.theme_row.add_widget(self.theme_dark_btn)
        
        # Notifications row
        self.notif_row = BoxLayout(
            orientation="horizontal", 
            size_hint_y=None,
            height=dp(40)
        )
        
        self.notif_label = Label(
            text="Notifications:",
            size_hint_x=0.7,
            halign="left",
            text_size=(dp(350), dp(40))
        )
        
        self.notif_switch = Switch(
            active=self.notifications_enabled,
            size_hint_x=0.3
        )
        self.notif_switch.bind(active=self.toggle_notifications)
        
        self.notif_row.add_widget(self.notif_label)
        self.notif_row.add_widget(self.notif_switch)
        
        self.display_section.add_widget(self.display_header)
        self.display_section.add_widget(self.odds_row)
        self.display_section.add_widget(self.theme_row)
        self.display_section.add_widget(self.notif_row)
        
        # Data management section
        self.data_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(130),
            spacing=dp(10)
        )
        
        self.data_header = Label(
            text="Data Management",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            halign="left",
            text_size=(dp(500), dp(30))
        )
        
        self.refresh_btn = Button(
            text="Refresh Odds Data",
            size_hint_y=None,
            height=dp(40)
        )
        self.refresh_btn.bind(on_release=self.refresh_odds_data)
        
        self.clear_btn = Button(
            text="Clear All Data",
            size_hint_y=None,
            height=dp(40),
            background_color=[0.8, 0.2, 0.2, 1]
        )
        self.clear_btn.bind(on_release=self.confirm_clear_data)
        
        self.data_section.add_widget(self.data_header)
        self.data_section.add_widget(self.refresh_btn)
        self.data_section.add_widget(self.clear_btn)
        
        # About section
        self.about_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(100),
            spacing=dp(10)
        )
        
        self.about_header = Label(
            text="About",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(18),
            halign="left",
            text_size=(dp(500), dp(30))
        )
        
        self.about_btn = Button(
            text="About BettingBuddy",
            size_hint_y=None,
            height=dp(40)
        )
        self.about_btn.bind(on_release=self.show_about)
        
        self.about_section.add_widget(self.about_header)
        self.about_section.add_widget(self.about_btn)
        
        # Add all sections to content
        self.content.add_widget(self.api_section)
        self.content.add_widget(self.display_section)
        self.content.add_widget(self.data_section)
        self.content.add_widget(self.about_section)
        
        # Add scrollable content area
        self.scroll_view = BoxLayout()
        self.scroll_view.add_widget(self.content)
        self.layout.add_widget(self.scroll_view)
        
        # Navigation bar
        self.navbar = NavigationBar(active_button="settings")
        self.layout.add_widget(self.navbar)
        
        self.add_widget(self.layout)
    
    def on_pre_enter(self):
        """Load settings before entering screen."""
        # Set navbar active button
        self.navbar.active_button = "settings"
        self.navbar.update_buttons()
        
        # Load current settings
        self.load_settings()
    
    def load_settings(self):
        """Load current settings from database."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Get user preferences
        prefs = db.get_user_preferences()
        
        if not prefs:
            return
        
        # Update UI to reflect current settings
        self.api_key = prefs.get("api_key", "")
        self.api_input.text = self.api_key
        
        # Set odds format buttons
        odds_format = prefs.get("odds_format", "american")
        app.odds_format = odds_format
        self.update_odds_format_buttons(odds_format)
        
        # Set theme buttons
        theme = prefs.get("theme", "light")
        self.update_theme_buttons(theme)
        
        # Set notifications switch
        notifications = bool(prefs.get("notification_enabled", 1))
        self.notifications_enabled = notifications
        self.notif_switch.active = notifications
    
    def update_odds_format_buttons(self, format_type):
        """Update the odds format button states."""
        app = self.manager.parent
        
        # Reset all buttons
        self.odds_american_btn.background_color = app.primary_color
        self.odds_decimal_btn.background_color = app.primary_color
        self.odds_fractional_btn.background_color = app.primary_color
        
        # Highlight the active format
        if format_type == "american":
            self.odds_american_btn.background_color = app.dark_primary_color
        elif format_type == "decimal":
            self.odds_decimal_btn.background_color = app.dark_primary_color
        elif format_type == "fractional":
            self.odds_fractional_btn.background_color = app.dark_primary_color
    
    def update_theme_buttons(self, theme):
        """Update the theme button states."""
        app = self.manager.parent
        
        # Reset all buttons
        self.theme_light_btn.background_color = app.primary_color
        self.theme_dark_btn.background_color = app.primary_color
        
        # Highlight the active theme
        if theme == "light":
            self.theme_light_btn.background_color = app.dark_primary_color
        else:
            self.theme_dark_btn.background_color = app.dark_primary_color
    
    def save_api_key(self, instance):
        """Save API key to database."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            self.show_message("Error", "Database connection not available")
            return
        
        # Get API key from input
        api_key = self.api_input.text.strip()
        
        # Save to database
        success = db.update_user_preferences(api_key=api_key)
        
        if success:
            # Update app's API service
            if hasattr(app, 'api_service') and app.api_service:
                app.api_service.set_api_key(api_key)
            
            self.show_message("Success", "API key saved successfully")
        else:
            self.show_message("Error", "Failed to save API key")
    
    def set_odds_format(self, format_type):
        """Set odds format preference."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Save to database
        success = db.update_user_preferences(odds_format=format_type)
        
        if success:
            # Update app's odds format
            app.odds_format = format_type
            
            # Update button states
            self.update_odds_format_buttons(format_type)
            
            self.show_message("Success", f"Odds format set to {format_type.capitalize()}")
        else:
            self.show_message("Error", "Failed to update odds format")
    
    def set_theme(self, theme):
        """Set theme preference."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Save to database
        success = db.update_user_preferences(theme=theme)
        
        if success:
            # Update button states
            self.update_theme_buttons(theme)
            
            # Theme would be applied here if we had theme support
            self.show_message("Success", f"Theme set to {theme.capitalize()}")
        else:
            self.show_message("Error", "Failed to update theme")
    
    def toggle_notifications(self, instance, value):
        """Toggle notifications setting."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Save to database
        success = db.update_user_preferences(notification_enabled=1 if value else 0)
        
        if success:
            self.notifications_enabled = value
        else:
            # Revert switch if save failed
            self.notif_switch.active = not value
            self.show_message("Error", "Failed to update notification settings")
    
    def refresh_odds_data(self, instance):
        """Refresh odds data from API."""
        app = self.manager.parent
        
        # Show loading message
        self.show_message("Refreshing Data", "Contacting API server for the latest odds data...")
        
        # Schedule the actual refresh
        Clock.schedule_once(self._perform_refresh, 0.5)
    
    def _perform_refresh(self, dt):
        """Perform the actual data refresh."""
        app = self.manager.parent
        
        # Check if API key is set
        if not self.api_key:
            self.show_message("Error", "API key not set. Please enter your API key first.")
            return
            
        try:
            # Import the init function
            from api_data_init import init_database
            
            # Initialize database with fresh API data
            success = init_database()
            
            if success:
                self.show_message("Success", "Odds data refreshed successfully")
            else:
                self.show_message("Error", "Failed to refresh odds data. Check API key and connection.")
                
        except Exception as e:
            self.show_message("Error", f"An error occurred: {str(e)}")
    
    def confirm_clear_data(self, instance):
        """Confirm data clearing."""
        # Create confirmation popup
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        warning = Label(
            text="WARNING: This will delete all your bets, parlays, and preferences. This action cannot be undone.",
            size_hint_y=None,
            height=dp(80),
            text_size=(dp(400), dp(80)),
            halign="center"
        )
        
        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        cancel_btn = Button(text="Cancel")
        clear_btn = Button(
            text="Clear Everything",
            background_color=[0.8, 0.2, 0.2, 1]
        )
        
        buttons.add_widget(cancel_btn)
        buttons.add_widget(clear_btn)
        
        content.add_widget(warning)
        content.add_widget(buttons)
        
        popup = Popup(
            title="Confirm Data Reset",
            content=content,
            size_hint=(0.9, 0.4),
            auto_dismiss=True
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        clear_btn.bind(on_release=lambda x: self.clear_all_data(popup))
        
        popup.open()
    
    def clear_all_data(self, popup):
        """Clear all app data."""
        popup.dismiss()
        
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        try:
            # Delete all data
            db.execute("DELETE FROM parlay_bets")
            db.execute("DELETE FROM parlays")
            db.execute("DELETE FROM bets")
            db.execute("DELETE FROM teams")
            db.execute("DELETE FROM sports")
            db.execute("DELETE FROM user_preferences")
            
            # Commit changes
            db.commit()
            
            # Re-create default preferences
            db.execute(
                "INSERT INTO user_preferences (odds_format, theme, notification_enabled) VALUES (?, ?, ?)",
                ('american', 'light', 1)
            )
            db.commit()
            
            # Show success message
            self.show_message("Data Cleared", "All data has been deleted. The app will restart with default settings.")
            
            # Schedule app restart
            Clock.schedule_once(self.restart_app, 2)
            
        except Exception as e:
            self.show_message("Error", f"Failed to clear data: {str(e)}")
    
    def restart_app(self, dt):
        """Restart the app by reinitializing."""
        app = self.manager.parent
        app.initialize_app(None)
    
    def show_about(self, instance):
        """Show about screen."""
        self.manager.current = "about"
    
    def show_message(self, title, message):
        """Show a message popup."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        msg_label = Label(
            text=message,
            size_hint_y=None,
            height=dp(50),
            halign="center",
            valign="middle",
            text_size=(dp(400), dp(50))
        )
        
        close_btn = Button(
            text="OK",
            size_hint_y=None,
            height=dp(50),
            size_hint_x=0.5,
            pos_hint={'center_x': 0.5}
        )
        
        content.add_widget(msg_label)
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        
        close_btn.bind(on_release=popup.dismiss)
        popup.open()
