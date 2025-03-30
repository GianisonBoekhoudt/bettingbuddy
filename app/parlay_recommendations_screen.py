"""
BettingBuddy Parlay Recommendations Screen

This module contains the UI for displaying parlay recommendations
based on specific criteria.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Rectangle

from datetime import datetime
import json

from models import Bet, Parlay, Team, UserPreferences
from database import BettingDatabase, calculate_parlay_odds, calculate_payout
from parlay_recommendations import ParlayRecommender
from animations import fade_in, slide_in_right, slide_in_left, pulse, bounce_in

class RecommendedParlayCard(BoxLayout):
    """Widget representing a recommended parlay."""
    
    parlay_type = StringProperty('')
    odds = StringProperty('')
    win_probability = NumericProperty(0.0)
    expected_value = NumericProperty(0.0)
    
    def __init__(self, **kwargs):
        super(RecommendedParlayCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(15)
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(280)  # Taller to fit more legs
        
        # Set background color
        with self.canvas.before:
            Color(*get_color_from_hex('#FFFFFF'))
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        # Update rectangle position and size when the layout changes
        def update_rect(instance, value):
            self.rect.pos = instance.pos
            self.rect.size = instance.size
        
        self.bind(pos=update_rect, size=update_rect)
        
        # Header - Parlay Type and Odds
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40)
        )
        
        self.type_label = Label(
            text=self.parlay_type,
            font_size=dp(16),
            bold=True,
            size_hint=(0.6, 1),
            halign='left',
            text_size=(None, dp(40))
        )
        
        self.odds_label = Label(
            text=self.odds,
            font_size=dp(16),
            bold=True,
            size_hint=(0.4, 1),
            halign='right',
            text_size=(None, dp(40))
        )
        
        header.add_widget(self.type_label)
        header.add_widget(self.odds_label)
        
        # Container for bet items
        self.bets_container = GridLayout(
            cols=1,
            size_hint=(1, None),
            height=dp(150),
            spacing=dp(5)
        )
        
        # Info grid for win probability and EV
        info_grid = GridLayout(
            cols=2,
            size_hint=(1, None),
            height=dp(40),
            spacing=[dp(10), dp(5)]
        )
        
        # Win probability
        info_grid.add_widget(Label(
            text='Win Probability:',
            halign='left',
            valign='middle',
            text_size=(None, dp(20))
        ))
        
        self.prob_label = Label(
            text=f"{self.win_probability:.1f}%",
            halign='right',
            valign='middle',
            text_size=(None, dp(20))
        )
        info_grid.add_widget(self.prob_label)
        
        # Expected value
        info_grid.add_widget(Label(
            text='Expected Value:',
            halign='left',
            valign='middle',
            text_size=(None, dp(20))
        ))
        
        self.ev_label = Label(
            text=f"{self.expected_value:.1f}%",
            halign='right',
            valign='middle',
            text_size=(None, dp(20)),
            color=get_color_from_hex('#4CAF50') if self.expected_value > 0 else get_color_from_hex('#F44336')
        )
        info_grid.add_widget(self.ev_label)
        
        # Create parlay button
        self.create_btn = Button(
            text='Create Parlay',
            size_hint=(1, None),
            height=dp(40),
            background_color=get_color_from_hex('#4CAF50')
        )
        
        # Add all components
        self.add_widget(header)
        self.add_widget(self.bets_container)
        self.add_widget(info_grid)
        self.add_widget(self.create_btn)
        
        # Bind properties
        self.bind(parlay_type=self.update_type_label)
        self.bind(odds=self.update_odds_label)
        self.bind(win_probability=self.update_probability_label)
        self.bind(expected_value=self.update_ev_label)
    
    def add_bet_item(self, team_name, odds):
        """Add a bet item to the parlay card."""
        bet_item = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30)
        )
        
        team_label = Label(
            text=team_name,
            size_hint=(0.7, 1),
            halign='left',
            text_size=(None, dp(30))
        )
        
        odds_label = Label(
            text=odds,
            size_hint=(0.3, 1),
            halign='right',
            text_size=(None, dp(30))
        )
        
        bet_item.add_widget(team_label)
        bet_item.add_widget(odds_label)
        
        self.bets_container.add_widget(bet_item)
        return bet_item
    
    def update_type_label(self, instance, value):
        self.type_label.text = value
    
    def update_odds_label(self, instance, value):
        self.odds_label.text = value
    
    def update_probability_label(self, instance, value):
        self.prob_label.text = f"{value:.1f}%"
    
    def update_ev_label(self, instance, value):
        self.ev_label.text = f"{value:.1f}%"
        self.ev_label.color = get_color_from_hex('#4CAF50') if value > 0 else get_color_from_hex('#F44336')
    
    def clear_bets(self):
        """Clear all bet items."""
        self.bets_container.clear_widgets()


class ParlayRecommendationsScreen(Screen):
    """Screen for displaying parlay recommendations."""
    
    def __init__(self, **kwargs):
        super(ParlayRecommendationsScreen, self).__init__(**kwargs)
        
        # Import animations to avoid circular import
        from animations import fade_in, slide_in_right, slide_in_left, bounce_in
        self.animations = {
            'fade_in': fade_in,
            'slide_in_right': slide_in_right,
            'slide_in_left': slide_in_left,
            'bounce_in': bounce_in
        }
        
        # Create the recommender
        self.recommender = ParlayRecommender()
        
        # Create main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Top bar
        top_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(15), dp(10)]
        )
        
        # Set background color using canvas
        with top_bar.canvas.before:
            Color(*get_color_from_hex('#2196F3'))
            self.top_bar_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)
        
        # Update rectangle position and size when the layout changes
        def update_rect(instance, value):
            self.top_bar_rect.pos = instance.pos
            self.top_bar_rect.size = instance.size
            
        top_bar.bind(pos=update_rect, size=update_rect)
        
        title_label = Label(
            text='Parlay Recommendations',
            font_size=dp(18),
            size_hint=(0.8, 1)
        )
        
        refresh_btn = Button(
            text='↻',
            size_hint=(0.2, None),
            height=dp(40),
            background_color=get_color_from_hex('#4CAF50')
        )
        refresh_btn.bind(on_press=self.refresh_recommendations)
        
        top_bar.add_widget(title_label)
        top_bar.add_widget(refresh_btn)
        
        # Create tab buttons for different recommendation types
        tabs_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(5), dp(5)]
        )
        
        self.two_leg_btn = Button(
            text='2-Leg Parlays',
            size_hint=(1, 1),
            background_color=get_color_from_hex('#4CAF50'),
            color=get_color_from_hex('#FFFFFF')
        )
        self.two_leg_btn.bind(on_press=lambda x: self.switch_tab('two_leg'))
        
        self.three_leg_btn = Button(
            text='3-Leg Parlays',
            size_hint=(1, 1),
            background_color=get_color_from_hex('#DDDDDD')
        )
        self.three_leg_btn.bind(on_press=lambda x: self.switch_tab('three_leg'))
        
        self.favorites_btn = Button(
            text='6-Leg Favorites',
            size_hint=(1, 1),
            background_color=get_color_from_hex('#DDDDDD')
        )
        self.favorites_btn.bind(on_press=lambda x: self.switch_tab('favorites'))
        
        tabs_bar.add_widget(self.two_leg_btn)
        tabs_bar.add_widget(self.three_leg_btn)
        tabs_bar.add_widget(self.favorites_btn)
        
        # Scrollable content for recommendations
        scroll_view = ScrollView(size_hint=(1, 1))
        self.content = GridLayout(
            cols=1,
            spacing=dp(15),
            padding=dp(15),
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        scroll_view.add_widget(self.content)
        
        # Bottom button
        back_btn = Button(
            text='Back',
            size_hint=(1, None),
            height=dp(50),
            background_color=get_color_from_hex('#9E9E9E')
        )
        back_btn.bind(on_press=self.go_back)
        
        # Add all components to the main layout
        main_layout.add_widget(top_bar)
        main_layout.add_widget(tabs_bar)
        main_layout.add_widget(scroll_view)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
        
        # Store components for later access
        self.scroll_view = scroll_view
        self.tabs_bar = tabs_bar
        self.tab_buttons = {
            'two_leg': self.two_leg_btn,
            'three_leg': self.three_leg_btn,
            'favorites': self.favorites_btn
        }
        
        # Store recommendations data
        self.recommendations = {
            'two_leg_parlays': [],
            'three_leg_parlays': [],
            'favorite_parlays': []
        }
        
        # Current active tab
        self.current_tab = 'two_leg'
    
    def on_enter(self):
        """Called when screen is entered."""
        # Configure screen transition
        from animations import slide_transition
        slide_transition(self.manager, 'left')
        
        # Load recommendations
        Clock.schedule_once(lambda dt: self.load_recommendations(), 0.5)
    
    def switch_tab(self, tab_name):
        """Switch between recommendation tabs."""
        self.current_tab = tab_name
        
        # Update button colors
        for name, button in self.tab_buttons.items():
            if name == tab_name:
                button.background_color = get_color_from_hex('#4CAF50')  # Active
                button.color = get_color_from_hex('#FFFFFF')
            else:
                button.background_color = get_color_from_hex('#DDDDDD')  # Inactive
                button.color = get_color_from_hex('#000000')
        
        # Display recommendations for selected tab
        self.display_recommendations()
    
    def load_recommendations(self):
        """Load parlay recommendations from the database."""
        try:
            # Show loading message
            self.content.clear_widgets()
            loading_label = Label(
                text='Loading recommendations...',
                size_hint_y=None,
                height=dp(100)
            )
            self.content.add_widget(loading_label)
            
            # Load recommendations in a separate thread to prevent UI freezing
            Clock.schedule_once(lambda dt: self._perform_loading(), 0.1)
            
        except Exception as e:
            print(f"Error loading recommendations: {e}")
            self.content.clear_widgets()
            error_label = Label(
                text=f"Error loading recommendations: {e}",
                size_hint_y=None,
                height=dp(100)
            )
            self.content.add_widget(error_label)
    
    def _perform_loading(self):
        """Perform the actual loading of recommendations."""
        try:
            # Get recommendations
            self.recommendations = self.recommender.get_recommendations_from_models()
            
            # Display recommendations for current tab
            self.display_recommendations()
            
        except Exception as e:
            print(f"Error loading recommendations: {e}")
            self.content.clear_widgets()
            error_label = Label(
                text=f"Error loading recommendations: {e}",
                size_hint_y=None,
                height=dp(100)
            )
            self.content.add_widget(error_label)
    
    def display_recommendations(self):
        """Display the recommendations for the current tab."""
        self.content.clear_widgets()
        
        # Get the right set of recommendations based on current tab
        recs = []
        if self.current_tab == 'two_leg':
            recs = self.recommendations['two_leg_parlays']
            if not recs:
                self.add_no_recommendations_label("No 2-leg parlay recommendations found.")
                return
        elif self.current_tab == 'three_leg':
            recs = self.recommendations['three_leg_parlays']
            if not recs:
                self.add_no_recommendations_label("No 3-leg parlay recommendations found.")
                return
        elif self.current_tab == 'favorites':
            recs = self.recommendations['favorite_parlays']
            if not recs:
                self.add_no_recommendations_label("No favorite parlay recommendations found.")
                return
        
        # Create a card for each recommendation
        for i, rec in enumerate(recs):
            card = self.create_recommendation_card(rec)
            card.opacity = 0  # Start invisible for animation
            self.content.add_widget(card)
            
            # Schedule staggered animations
            delay = i * 0.15
            Clock.schedule_once(lambda dt, widget=card: self.animations['fade_in'](widget), delay)
            
            # Store the recommendation data with the card for later access
            card.recommendation_data = rec
            
            # Bind the create button
            card.create_btn.bind(on_press=lambda btn, data=rec: self.create_parlay(data))
    
    def add_no_recommendations_label(self, message):
        """Add a label when no recommendations are available."""
        label = Label(
            text=message,
            size_hint_y=None,
            height=dp(100)
        )
        self.content.add_widget(label)
    
    def create_recommendation_card(self, recommendation):
        """Create a card for a parlay recommendation."""
        card = RecommendedParlayCard()
        
        # Set properties
        card.parlay_type = recommendation['type']
        card.odds = recommendation['american_odds']
        card.win_probability = recommendation['win_probability']
        card.expected_value = recommendation['ev']
        
        # Clear and add bet items
        card.clear_bets()
        for bet in recommendation['bets']:
            card.add_bet_item(bet['team_name'], bet['odds'])
        
        return card
    
    def create_parlay(self, recommendation):
        """Create a parlay from a recommendation."""
        try:
            # Extract bet IDs from recommendation
            bet_ids = [bet['bet_id'] for bet in recommendation['bets'] if 'bet_id' in bet]
            
            if not bet_ids:
                self.show_error_popup("Missing Bet IDs", "The recommendation does not contain valid bet IDs.")
                return
            
            # Get bets from database
            bets = []
            for bet_id in bet_ids:
                bet = Bet.get_by_id(bet_id)
                if bet:
                    bets.append(bet)
            
            if len(bets) < 2:
                self.show_error_popup("Invalid Bets", "Could not find enough valid bets for a parlay.")
                return
            
            # Create parlay with default stake of $10
            parlay = Parlay(bets=bets, stake=10.0)
            
            # Calculate odds and payout
            parlay.calculate_odds()
            parlay.calculate_payout()
            
            # Save to database
            parlay.save()
            
            # Show success popup
            popup = Popup(
                title='Success',
                content=Label(text='Parlay created successfully!'),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            
        except Exception as e:
            self.show_error_popup("Error", f"Failed to create parlay: {e}")
    
    def refresh_recommendations(self, instance=None):
        """Refresh the recommendations."""
        self.load_recommendations()
    
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