#!/usr/bin/env python3
"""
Screens Module for BettingBuddy app.

Contains general-purpose screen classes.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, BooleanProperty


class LoadingScreen(Screen):
    """Loading screen displayed while app is initializing."""
    
    loading_message = StringProperty("Loading app...")
    
    def update_status(self, message):
        """Update the loading status message."""
        self.loading_message = message


class AboutScreen(Screen):
    """About screen with app information."""
    
    version = StringProperty("v0.1.0")
    about_text = StringProperty(
        "BettingBuddy is a sports betting analysis and tracking app that helps you "
        "find value in betting opportunities and create optimal parlays. The app "
        "analyzes odds and provides recommendations based on mathematical models.\n\n"
        
        "Features:\n"
        "• Track betting opportunities across multiple sports\n"
        "• Get parlay recommendations based on value analysis\n"
        "• Monitor your betting history and performance\n"
        "• Analyze implied probabilities and find value bets\n\n"
        
        "This app is for informational and entertainment purposes only. "
        "Please gamble responsibly."
    )


class ErrorScreen(Screen):
    """Error screen displayed when app encounters an error."""
    
    error_message = StringProperty("An error occurred. Please try again.")
    
    def try_again(self):
        """Attempt to restart the app."""
        app = self.manager.parent.app
        app.initialize_app(None)


class NavigationBar(BoxLayout):
    """Navigation bar widget used across screens."""
    
    active_button = StringProperty("home")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(10)
        
        # Home button
        self.home_btn = Button(
            text="Home",
            on_release=self.switch_to_home,
            size_hint_x=1
        )
        
        # Bets button
        self.bets_btn = Button(
            text="Bets",
            on_release=self.switch_to_bets,
            size_hint_x=1
        )
        
        # Parlays button
        self.parlays_btn = Button(
            text="Parlays",
            on_release=self.switch_to_parlays,
            size_hint_x=1
        )
        
        # Settings button
        self.settings_btn = Button(
            text="Settings",
            on_release=self.switch_to_settings,
            size_hint_x=1
        )
        
        self.add_widget(self.home_btn)
        self.add_widget(self.bets_btn)
        self.add_widget(self.parlays_btn)
        self.add_widget(self.settings_btn)
        
        # Set active button
        self.update_buttons()
    
    def update_buttons(self):
        """Update button styles based on active button."""
        buttons = {
            "home": self.home_btn,
            "bets": self.bets_btn,
            "parlays": self.parlays_btn,
            "settings": self.settings_btn
        }
        
        app = self.parent.manager.parent
        
        for name, btn in buttons.items():
            if name == self.active_button:
                btn.background_color = app.dark_primary_color
            else:
                btn.background_color = app.primary_color
    
    def switch_to_home(self, instance):
        """Switch to home screen."""
        self.active_button = "home"
        self.update_buttons()
        self.parent.manager.current = "home"
    
    def switch_to_bets(self, instance):
        """Switch to bets screen."""
        self.active_button = "bets"
        self.update_buttons()
        self.parent.manager.current = "bets"
    
    def switch_to_parlays(self, instance):
        """Switch to parlays screen."""
        self.active_button = "parlays"
        self.update_buttons()
        self.parent.manager.current = "parlays"
    
    def switch_to_settings(self, instance):
        """Switch to settings screen."""
        self.active_button = "settings"
        self.update_buttons()
        self.parent.manager.current = "settings"


class HeaderBar(BoxLayout):
    """Header bar widget with title and optional back button."""
    
    title = StringProperty("BettingBuddy")
    show_back = BooleanProperty(False)
    back_screen = StringProperty("home")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(10), dp(5)]
        
        # Back button
        self.back_btn = Button(
            text="< Back",
            on_release=self.go_back,
            size_hint_x=None,
            width=dp(80),
            opacity=1 if self.show_back else 0,
            disabled=not self.show_back
        )
        
        # Title label
        self.title_label = Label(
            text=self.title,
            font_size=dp(18),
            size_hint_x=1,
            halign="center"
        )
        
        # Spacer for alignment
        self.spacer = Button(
            text="",
            disabled=True,
            background_color=(0, 0, 0, 0),
            size_hint_x=None,
            width=dp(80) if self.show_back else 0
        )
        
        self.add_widget(self.back_btn)
        self.add_widget(self.title_label)
        self.add_widget(self.spacer)
        
        # Bind properties for updates
        self.bind(title=self.update_title)
        self.bind(show_back=self.update_back_button)
    
    def update_title(self, instance, value):
        """Update the title label."""
        self.title_label.text = value
    
    def update_back_button(self, instance, value):
        """Update back button visibility."""
        self.back_btn.opacity = 1 if value else 0
        self.back_btn.disabled = not value
        self.spacer.width = dp(80) if value else 0
    
    def go_back(self, instance):
        """Go back to previous screen."""
        self.parent.manager.current = self.back_screen
