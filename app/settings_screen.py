"""
BettingBuddy Settings Screen

This module contains the settings screen UI components.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.clock import Clock

from models import UserPreferences
from api_service import APIService
from odds_updater import OddsUpdateManager

class SettingsScreen(Screen):
    """Settings screen for the app."""
    
    def __init__(self, odds_updater=None, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.odds_updater = odds_updater
        self.api_service = APIService()
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Settings title
        title = Label(
            text='Settings',
            font_size=dp(24),
            size_hint=(1, None),
            height=dp(50)
        )
        
        # Create settings grid
        settings_layout = GridLayout(
            cols=1,
            spacing=dp(15),
            size_hint=(1, 1)
        )
        
        # Add API Key section
        api_key_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            spacing=dp(5)
        )
        
        api_key_layout.add_widget(Label(
            text='The Odds API Key',
            font_size=dp(18),
            size_hint=(1, None),
            height=dp(30),
            halign='left'
        ))
        
        api_key_desc = Label(
            text='Enter your API key from api.the-odds-api.com',
            font_size=dp(14),
            size_hint=(1, None),
            height=dp(20),
            halign='left',
            color=get_color_from_hex('#666666')
        )
        api_key_layout.add_widget(api_key_desc)
        
        # API Key input
        self.api_key_input = TextInput(
            hint_text='Enter API Key',
            multiline=False,
            password=True,  # Hide API key
            size_hint=(1, None),
            height=dp(40)
        )
        api_key_layout.add_widget(self.api_key_input)
        
        # Add toggle to show/hide API key
        show_key_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30)
        )
        
        show_key_layout.add_widget(Label(
            text='Show API Key',
            size_hint=(0.7, 1),
            halign='left'
        ))
        
        self.show_key_switch = Switch(
            active=False,
            size_hint=(0.3, 1)
        )
        self.show_key_switch.bind(active=self.toggle_show_api_key)
        show_key_layout.add_widget(self.show_key_switch)
        
        api_key_layout.add_widget(show_key_layout)
        
        # Odds Update Settings
        odds_update_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(150),
            spacing=dp(5)
        )
        
        odds_update_layout.add_widget(Label(
            text='Odds Update Settings',
            font_size=dp(18),
            size_hint=(1, None),
            height=dp(30),
            halign='left'
        ))
        
        # Enable automatic updates
        auto_update_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30)
        )
        
        auto_update_layout.add_widget(Label(
            text='Enable Automatic Updates',
            size_hint=(0.7, 1),
            halign='left'
        ))
        
        self.auto_update_switch = Switch(
            active=True,
            size_hint=(0.3, 1)
        )
        auto_update_layout.add_widget(self.auto_update_switch)
        
        odds_update_layout.add_widget(auto_update_layout)
        
        # Update interval
        interval_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40)
        )
        
        interval_layout.add_widget(Label(
            text='Update Interval',
            size_hint=(0.5, 1),
            halign='left'
        ))
        
        # Dropdown for update interval
        self.interval_spinner = Spinner(
            text='1 hour',
            values=['1 minute', '5 minutes', '15 minutes', '30 minutes', '1 hour'],
            size_hint=(0.5, 1)
        )
        interval_layout.add_widget(self.interval_spinner)
        
        odds_update_layout.add_widget(interval_layout)
        
        # Manual update button
        manual_update_btn = Button(
            text='Update Odds Now',
            size_hint=(1, None),
            height=dp(50),
            background_color=get_color_from_hex('#4CAF50')
        )
        manual_update_btn.bind(on_press=self.manual_update_odds)
        odds_update_layout.add_widget(manual_update_btn)
        
        # Test API button
        test_api_btn = Button(
            text='Test API Connection',
            size_hint=(1, None),
            height=dp(50),
            background_color=get_color_from_hex('#2196F3')
        )
        test_api_btn.bind(on_press=self.test_api_connection)
        
        # Save settings button
        save_btn = Button(
            text='Save Settings',
            size_hint=(1, None),
            height=dp(60),
            background_color=get_color_from_hex('#4CAF50')
        )
        save_btn.bind(on_press=self.save_settings)
        
        # Back button
        back_btn = Button(
            text='Back',
            size_hint=(1, None),
            height=dp(60),
            background_color=get_color_from_hex('#9E9E9E')
        )
        back_btn.bind(on_press=self.go_back)
        
        # Add all sections to the settings layout
        settings_layout.add_widget(api_key_layout)
        settings_layout.add_widget(odds_update_layout)
        settings_layout.add_widget(test_api_btn)
        
        # Add layouts to main layout
        layout.add_widget(title)
        layout.add_widget(settings_layout)
        layout.add_widget(save_btn)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
        
        # Load settings when the screen is created
        Clock.schedule_once(lambda dt: self.load_settings(), 0.1)
    
    def on_enter(self):
        """Called when the screen is entered."""
        # Refresh settings
        self.load_settings()
    
    def load_settings(self):
        """Load settings from UserPreferences."""
        prefs = UserPreferences.get()
        
        # Set API key
        if prefs.api_key:
            self.api_key_input.text = prefs.api_key
        
        # Set update settings
        auto_update = prefs.preferences.get('auto_update_odds', True)
        self.auto_update_switch.active = auto_update
        
        # Set update interval - default to 1 hour (3600 seconds)
        interval_seconds = prefs.preferences.get('odds_update_interval', 3600)
        interval_text = self._seconds_to_interval_text(interval_seconds)
        self.interval_spinner.text = interval_text
    
    def toggle_show_api_key(self, instance, value):
        """Toggle showing/hiding the API key."""
        self.api_key_input.password = not value
    
    def manual_update_odds(self, instance):
        """Manually update odds."""
        # Check if we have an API key
        api_key = self.api_key_input.text.strip()
        if not api_key:
            self.show_error_popup('API Key Required', 'Please enter your API key to update odds.')
            return
        
        # If odds_updater is available, use it to update odds
        if self.odds_updater:
            # Set the API key
            self.odds_updater.set_api_key(api_key)
            
            # Show progress popup
            popup = Popup(
                title='Updating Odds',
                content=Label(text='Fetching latest odds...'),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            
            # Schedule the update
            def update_odds(dt):
                try:
                    self.odds_updater.update_now()
                    popup.dismiss()
                    self.show_success_popup('Odds Updated', 'Successfully updated odds for all bets.')
                except Exception as e:
                    popup.dismiss()
                    self.show_error_popup('Update Failed', f'Failed to update odds: {e}')
            
            Clock.schedule_once(update_odds, 0.5)
        else:
            self.show_error_popup('Not Available', 'Odds updater is not available. Please restart the app.')
    
    def test_api_connection(self, instance):
        """Test the API connection."""
        # Check if we have an API key
        api_key = self.api_key_input.text.strip()
        if not api_key:
            self.show_error_popup('API Key Required', 'Please enter your API key to test the connection.')
            return
        
        # Show progress popup
        popup = Popup(
            title='Testing API',
            content=Label(text='Testing connection to The Odds API...'),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
        # Test the connection
        def test_connection(dt):
            try:
                self.api_service.set_api_key(api_key)
                # Try to get sports list
                sports = self.api_service.get_sports()
                
                if sports:
                    popup.dismiss()
                    self.show_success_popup('Connection Successful', 
                                          f'Successfully connected to The Odds API. '
                                          f'Found {len(sports)} sports.')
                else:
                    popup.dismiss()
                    self.show_error_popup('Test Failed', 'Connected to API but received no data.')
            except Exception as e:
                popup.dismiss()
                self.show_error_popup('Connection Failed', f'Failed to connect to The Odds API: {e}')
        
        Clock.schedule_once(test_connection, 0.5)
    
    def save_settings(self, instance):
        """Save settings to UserPreferences."""
        # Get API key
        api_key = self.api_key_input.text.strip()
        
        # Get update settings
        auto_update = self.auto_update_switch.active
        interval_seconds = self._interval_text_to_seconds(self.interval_spinner.text)
        
        # Create preferences
        prefs = UserPreferences.get()
        prefs.api_key = api_key
        
        if 'preferences' not in prefs.__dict__ or prefs.preferences is None:
            prefs.preferences = {}
        
        prefs.preferences['auto_update_odds'] = auto_update
        prefs.preferences['odds_update_interval'] = interval_seconds
        
        # Save preferences
        success = prefs.save()
        
        if success:
            # Update odds updater if available
            if self.odds_updater:
                self.odds_updater.set_api_key(api_key)
                
                if auto_update:
                    self.odds_updater.start_updates(interval=interval_seconds)
                else:
                    self.odds_updater.stop_updates()
            
            self.show_success_popup('Settings Saved', 'Your settings have been saved successfully.')
        else:
            self.show_error_popup('Save Failed', 'Failed to save settings. Please try again.')
    
    def go_back(self, instance):
        """Go back to the previous screen."""
        self.manager.current = 'main'
    
    def show_error_popup(self, title, message):
        """Show an error popup."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def show_success_popup(self, title, message):
        """Show a success popup."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def _seconds_to_interval_text(self, seconds):
        """Convert seconds to interval text."""
        if seconds <= 60:
            return '1 minute'
        elif seconds <= 300:
            return '5 minutes'
        elif seconds <= 900:
            return '15 minutes'
        elif seconds <= 1800:
            return '30 minutes'
        else:
            return '1 hour'
    
    def _interval_text_to_seconds(self, text):
        """Convert interval text to seconds."""
        if text == '1 minute':
            return 60
        elif text == '5 minutes':
            return 300
        elif text == '15 minutes':
            return 900
        elif text == '30 minutes':
            return 1800
        elif text == '1 hour':
            return 3600
        else:
            return 3600  # Default to 1 hour