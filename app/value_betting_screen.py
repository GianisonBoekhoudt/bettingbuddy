"""
BettingBuddy Value Betting Screen

This module contains the UI components for value betting analysis.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.slider import Slider
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, Rectangle

from datetime import datetime
import json

from models import Bet, Parlay, Team, Sport, UserPreferences
from database import BettingDatabase, calculate_parlay_odds, calculate_payout
from value_betting import ValueBettingAnalyzer, ValueBettingStrategy
from api_service import APIService
from animations import fade_in, fade_out, slide_in_right, pulse, bounce_in

class ValueBetItem(BoxLayout):
    """Widget representing a value bet item."""
    
    team_name = StringProperty('')
    odds = StringProperty('')
    expected_value = NumericProperty(0)
    is_value_bet = BooleanProperty(False)
    confidence = NumericProperty(0)
    recommended_stake = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super(ValueBetItem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        self.size_hint_y = None
        self.height = dp(130)
        
        # Top row with team and odds
        top_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30)
        )
        
        self.team_label = Label(
            text=self.team_name,
            size_hint=(0.7, 1),
            halign='left',
            text_size=(None, dp(30)),
            bold=True
        )
        
        self.odds_label = Label(
            text=self.odds,
            size_hint=(0.3, 1),
            halign='right',
            text_size=(None, dp(30)),
            bold=True
        )
        
        top_row.add_widget(self.team_label)
        top_row.add_widget(self.odds_label)
        
        # Middle row with stats
        stats_row = GridLayout(
            cols=2,
            size_hint=(1, None),
            height=dp(60),
            spacing=[dp(10), dp(5)]
        )
        
        # EV label
        stats_row.add_widget(Label(
            text='Expected Value:',
            halign='left',
            valign='middle',
            text_size=(None, dp(20))
        ))
        
        self.ev_label = Label(
            text=f"{self.expected_value:.2f}%",
            halign='right',
            valign='middle',
            text_size=(None, dp(20)),
            color=(0, 1, 0, 1) if self.expected_value > 0 else (1, 0, 0, 1)
        )
        stats_row.add_widget(self.ev_label)
        
        # Confidence label
        stats_row.add_widget(Label(
            text='Confidence:',
            halign='left',
            valign='middle',
            text_size=(None, dp(20))
        ))
        
        self.confidence_label = Label(
            text=f"{self.confidence:.2f}",
            halign='right',
            valign='middle',
            text_size=(None, dp(20))
        )
        stats_row.add_widget(self.confidence_label)
        
        # Stake label
        stats_row.add_widget(Label(
            text='Recommended Stake:',
            halign='left',
            valign='middle',
            text_size=(None, dp(20))
        ))
        
        self.stake_label = Label(
            text=f"${self.recommended_stake:.2f}",
            halign='right',
            valign='middle',
            text_size=(None, dp(20))
        )
        stats_row.add_widget(self.stake_label)
        
        # Bottom row with action button
        bottom_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(10)
        )
        
        self.add_bet_btn = Button(
            text='Add to Parlay',
            size_hint=(1, 1),
            background_color=get_color_from_hex('#4CAF50') if self.is_value_bet else get_color_from_hex('#9E9E9E')
        )
        
        bottom_row.add_widget(self.add_bet_btn)
        
        # Add all rows to the layout
        self.add_widget(top_row)
        self.add_widget(stats_row)
        self.add_widget(bottom_row)
        
        # Bind properties
        self.bind(team_name=self.update_team_label)
        self.bind(odds=self.update_odds_label)
        self.bind(expected_value=self.update_ev_label)
        self.bind(confidence=self.update_confidence_label)
        self.bind(recommended_stake=self.update_stake_label)
        self.bind(is_value_bet=self.update_button_color)
    
    def update_team_label(self, instance, value):
        self.team_label.text = value
    
    def update_odds_label(self, instance, value):
        self.odds_label.text = value
    
    def update_ev_label(self, instance, value):
        self.ev_label.text = f"{value:.2f}%"
        self.ev_label.color = (0, 1, 0, 1) if value > 0 else (1, 0, 0, 1)
    
    def update_confidence_label(self, instance, value):
        self.confidence_label.text = f"{value:.2f}"
    
    def update_stake_label(self, instance, value):
        self.stake_label.text = f"${value:.2f}"
    
    def update_button_color(self, instance, value):
        self.add_bet_btn.background_color = get_color_from_hex('#4CAF50') if value else get_color_from_hex('#9E9E9E')


class ValueBettingScreen(Screen):
    """Screen for value betting analysis."""
    
    def __init__(self, **kwargs):
        super(ValueBettingScreen, self).__init__(**kwargs)
        
        # Initialize services
        self.analyzer = ValueBettingAnalyzer()
        self.strategy = ValueBettingStrategy(analyzer=self.analyzer)
        self.api_service = APIService()
        
        # Create main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Create top bar
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
            text='Value Betting',
            font_size=dp(20),
            size_hint=(0.8, 1)
        )
        
        refresh_btn = Button(
            text='↻',
            size_hint=(0.2, None),
            height=dp(40),
            background_color=get_color_from_hex('#4CAF50')
        )
        refresh_btn.bind(on_press=self.refresh_value_bets)
        
        top_bar.add_widget(title_label)
        top_bar.add_widget(refresh_btn)
        
        # Settings section
        settings_layout = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(180),
            padding=dp(10),
            spacing=dp(5)
        )
        
        # Bankroll row
        bankroll_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40)
        )
        
        bankroll_row.add_widget(Label(
            text='Your Bankroll: $',
            size_hint=(0.4, 1)
        ))
        
        self.bankroll_input = TextInput(
            text='1000.00',
            input_filter='float',
            multiline=False,
            size_hint=(0.6, 1)
        )
        bankroll_row.add_widget(self.bankroll_input)
        
        # Strategy row
        strategy_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40)
        )
        
        strategy_row.add_widget(Label(
            text='Bankroll Strategy:',
            size_hint=(0.4, 1)
        ))
        
        # Strategy spinner
        from kivy.uix.spinner import Spinner
        self.strategy_spinner = Spinner(
            text='Kelly (safer)',
            values=['Kelly (safer)', 'Percentage', 'Flat Stake'],
            size_hint=(0.6, 1)
        )
        strategy_row.add_widget(self.strategy_spinner)
        
        # Confidence threshold row
        confidence_row = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60)
        )
        
        conf_label_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20)
        )
        
        conf_label_row.add_widget(Label(
            text='Confidence Threshold:',
            size_hint=(0.7, 1),
            halign='left'
        ))
        
        self.confidence_value_label = Label(
            text='60%',
            size_hint=(0.3, 1),
            halign='right'
        )
        conf_label_row.add_widget(self.confidence_value_label)
        
        # Slider for confidence
        self.confidence_slider = Slider(
            min=50,
            max=90,
            value=60,
            size_hint=(1, None),
            height=dp(40)
        )
        self.confidence_slider.bind(value=self.update_confidence_label)
        
        confidence_row.add_widget(conf_label_row)
        confidence_row.add_widget(self.confidence_slider)
        
        # Add rows to settings layout
        settings_layout.add_widget(bankroll_row)
        settings_layout.add_widget(strategy_row)
        settings_layout.add_widget(confidence_row)
        
        # Create scrollable content for value bets
        scroll_view = ScrollView(size_hint=(1, 1))
        self.value_bets_layout = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None
        )
        self.value_bets_layout.bind(minimum_height=self.value_bets_layout.setter('height'))
        scroll_view.add_widget(self.value_bets_layout)
        
        # Bottom buttons
        bottom_buttons = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10),
            padding=dp(10)
        )
        
        self.parlay_btn = Button(
            text='Create Value Parlay',
            size_hint=(0.5, 1),
            background_color=get_color_from_hex('#FF9800')
        )
        self.parlay_btn.bind(on_press=self.create_value_parlay)
        
        back_btn = Button(
            text='Back',
            size_hint=(0.5, 1),
            background_color=get_color_from_hex('#9E9E9E')
        )
        back_btn.bind(on_press=self.go_back)
        
        bottom_buttons.add_widget(self.parlay_btn)
        bottom_buttons.add_widget(back_btn)
        
        # Add all sections to the main layout
        main_layout.add_widget(top_bar)
        main_layout.add_widget(settings_layout)
        main_layout.add_widget(scroll_view)
        main_layout.add_widget(bottom_buttons)
        
        self.add_widget(main_layout)
        
        # Placeholder for selected value bets
        self.selected_value_bets = []
        
    def on_enter(self):
        """Called when the screen is entered."""
        self.load_settings()
        # Schedule loading value bets
        Clock.schedule_once(lambda dt: self.load_value_bets(), 0.5)
    
    def load_settings(self):
        """Load user settings."""
        prefs = UserPreferences.get()
        
        # Get saved bankroll
        saved_bankroll = prefs.preferences.get('bankroll', 1000.0)
        self.bankroll_input.text = str(saved_bankroll)
        
        # Get saved strategy
        strategy_type = prefs.preferences.get('bankroll_strategy', 'kelly')
        if strategy_type == 'kelly':
            self.strategy_spinner.text = 'Kelly (safer)'
        elif strategy_type == 'percentage':
            self.strategy_spinner.text = 'Percentage'
        else:
            self.strategy_spinner.text = 'Flat Stake'
        
        # Get saved confidence threshold
        conf_threshold = prefs.preferences.get('confidence_threshold', 60)
        self.confidence_slider.value = conf_threshold
    
    def update_confidence_label(self, instance, value):
        """Update confidence threshold label when slider changes."""
        self.confidence_value_label.text = f'{int(value)}%'
    
    def save_settings(self):
        """Save user settings."""
        try:
            # Get bankroll
            bankroll = float(self.bankroll_input.text)
            
            # Get strategy type
            strategy_text = self.strategy_spinner.text
            if strategy_text == 'Kelly (safer)':
                strategy_type = 'kelly'
            elif strategy_text == 'Percentage':
                strategy_type = 'percentage'
            else:
                strategy_type = 'flat'
            
            # Get confidence threshold
            conf_threshold = int(self.confidence_slider.value)
            
            # Save to preferences
            prefs = UserPreferences.get()
            
            if 'preferences' not in prefs.__dict__ or prefs.preferences is None:
                prefs.preferences = {}
            
            prefs.preferences['bankroll'] = bankroll
            prefs.preferences['bankroll_strategy'] = strategy_type
            prefs.preferences['confidence_threshold'] = conf_threshold
            
            # Save preferences
            prefs.save()
            
            # Update analyzer settings
            self.analyzer.set_params(confidence_threshold=conf_threshold/100)
            
            # Update strategy settings
            self.strategy.set_bankroll_strategy(
                strategy=strategy_type,
                stake_percentage=0.02 if strategy_type == 'flat' else 0.03,
                kelly_fraction=0.5 if strategy_type == 'kelly' else 0.8
            )
            
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_value_bets(self):
        """Load and display value bets."""
        # Save settings first
        self.save_settings()
        
        # Clear existing content
        self.value_bets_layout.clear_widgets()
        self.selected_value_bets = []
        
        # Show loading indicator
        loading_label = Label(
            text='Loading value bets...',
            size_hint_y=None,
            height=dp(80)
        )
        self.value_bets_layout.add_widget(loading_label)
        
        # Schedule actual loading
        Clock.schedule_once(lambda dt: self._perform_value_bet_loading(), 0.5)
    
    def _perform_value_bet_loading(self):
        """Perform the actual loading of value bets."""
        try:
            # Clear the layout again
            self.value_bets_layout.clear_widgets()
            
            # Get bankroll
            try:
                bankroll = float(self.bankroll_input.text)
            except ValueError:
                bankroll = 1000.0
            
            # Get active bets from database
            db = BettingDatabase()
            bets_data = db.get_active_bets()
            
            if not bets_data:
                # No bets available, show message
                no_bets_label = Label(
                    text='No active bets found. Create some bets first.',
                    size_hint_y=None,
                    height=dp(80)
                )
                self.value_bets_layout.add_widget(no_bets_label)
                return
            
            # Convert to format needed for value betting analysis
            available_bets = []
            for bet in bets_data:
                # Generate a simulated true probability for demonstration
                # In a real app, this would come from a model or user input
                team_name = bet.get('team_name', 'Unknown Team')
                odds = bet.get('odds', '+100')
                
                # Extract numerical part from odds
                import re
                odds_value = re.search(r'[+-]?\d+', odds)
                if odds_value:
                    odds_value = int(odds_value.group())
                    
                    # Generate a true probability that's slightly better than implied
                    from database import american_to_decimal
                    implied_prob = 1 / american_to_decimal(odds)
                    
                    # For demonstration, we'll make favorable odds seem more valuable
                    if odds_value > 0:  # Underdog
                        true_prob = implied_prob * (1 + 0.15)  # 15% edge on underdogs
                    else:  # Favorite
                        true_prob = implied_prob * (1 + 0.05)  # 5% edge on favorites
                    
                    # Cap at reasonable values
                    true_prob = min(0.95, max(0.05, true_prob))
                else:
                    true_prob = 0.5  # Default
                
                available_bets.append({
                    'team_name': team_name,
                    'odds': odds,
                    'true_probability': true_prob,
                    'sport': bet.get('sport_name', 'Unknown'),
                    'bet_id': bet.get('id'),
                    'event_date': bet.get('event_date')
                })
            
            # Generate betting plan
            betting_plan = self.strategy.generate_betting_plan(bankroll, available_bets)
            
            # Display value bets
            value_bets = betting_plan.get('value_bets', [])
            
            if not value_bets:
                no_value_label = Label(
                    text='No value bets found with current settings.',
                    size_hint_y=None,
                    height=dp(80)
                )
                self.value_bets_layout.add_widget(no_value_label)
                return
            
            # Add value bets to the layout with animations
            for i, bet in enumerate(value_bets):
                bet_item = ValueBetItem(
                    team_name=bet.get('team_name', 'Unknown'),
                    odds=bet.get('odds', '+100'),
                    expected_value=bet.get('ev', 0),
                    is_value_bet=bet.get('is_value_bet', False),
                    confidence=bet.get('confidence', 0),
                    recommended_stake=bet.get('recommended_stake', 0)
                )
                
                # Store the bet data for later use
                bet_item.bet_data = bet
                
                # Bind the add bet button
                bet_item.add_bet_btn.bind(on_press=lambda btn, item=bet_item: self.toggle_bet_selection(item))
                
                self.value_bets_layout.add_widget(bet_item)
                
                # Apply animation with increasing delay
                bet_item.opacity = 0
                Clock.schedule_once(
                    lambda dt, widget=bet_item: fade_in(widget, duration=0.3),
                    i * 0.1  # Staggered delay
                )
            
            # Update parlay button based on available value bets
            self.parlay_btn.disabled = len(value_bets) < 2
            
        except Exception as e:
            # Show error message
            error_label = Label(
                text=f'Error loading value bets: {e}',
                size_hint_y=None,
                height=dp(80)
            )
            self.value_bets_layout.add_widget(error_label)
    
    def toggle_bet_selection(self, bet_item):
        """Toggle selection of a value bet for parlay creation."""
        if bet_item in self.selected_value_bets:
            # Deselect
            self.selected_value_bets.remove(bet_item)
            bet_item.add_bet_btn.text = 'Add to Parlay'
            bet_item.add_bet_btn.background_color = get_color_from_hex('#4CAF50')
        else:
            # Select
            self.selected_value_bets.append(bet_item)
            bet_item.add_bet_btn.text = 'Selected ✓'
            bet_item.add_bet_btn.background_color = get_color_from_hex('#FF9800')
            
            # Apply pulse animation
            pulse(bet_item)
    
    def refresh_value_bets(self, instance=None):
        """Refresh value bets display."""
        self.load_value_bets()
    
    def create_value_parlay(self, instance):
        """Create a value parlay from selected bets."""
        if len(self.selected_value_bets) < 2:
            # Show error popup
            popup = Popup(
                title='Not Enough Bets',
                content=Label(text='Please select at least 2 bets for a parlay.'),
                size_hint=(0.8, 0.4)
            )
            popup.open()
            return
        
        # Get bet data from selected bets
        selected_bet_data = [item.bet_data for item in self.selected_value_bets]
        
        # Calculate combined probability and expected value
        combined_prob = 1.0
        for bet in selected_bet_data:
            combined_prob *= bet.get('true_probability', 0.5)
        
        # Calculate decimal odds
        from database import american_to_decimal, decimal_to_american
        decimal_odds = 1.0
        for bet in selected_bet_data:
            decimal_odds *= american_to_decimal(bet.get('odds', '+100'))
        
        # Calculate EV
        ev = (decimal_odds * combined_prob) - 1
        ev_percentage = ev * 100
        
        # Format parlay odds
        american_odds = decimal_to_american(decimal_odds)
        
        # Create popup content
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        title_label = Label(
            text='Value Parlay Analysis',
            font_size=dp(18),
            size_hint=(1, None),
            height=dp(30)
        )
        content.add_widget(title_label)
        
        # Bets list
        bets_layout = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint=(1, None)
        )
        bets_layout.bind(minimum_height=bets_layout.setter('height'))
        
        # Calculate total height based on number of bets
        bets_layout.height = len(selected_bet_data) * dp(30)
        
        for bet in selected_bet_data:
            bet_row = BoxLayout(
                orientation='horizontal',
                size_hint=(1, None),
                height=dp(30)
            )
            bet_row.add_widget(Label(
                text=bet.get('team_name', 'Unknown'),
                size_hint=(0.7, 1),
                halign='left',
                text_size=(None, dp(30))
            ))
            bet_row.add_widget(Label(
                text=bet.get('odds', '+100'),
                size_hint=(0.3, 1),
                halign='right',
                text_size=(None, dp(30))
            ))
            bets_layout.add_widget(bet_row)
        
        # Add bets to scrollview if there are many
        if len(selected_bet_data) > 5:
            scroll = ScrollView(size_hint=(1, None), height=dp(150))
            scroll.add_widget(bets_layout)
            content.add_widget(scroll)
        else:
            content.add_widget(bets_layout)
        
        # Stats grid
        stats_grid = GridLayout(
            cols=2,
            size_hint=(1, None),
            height=dp(90),
            spacing=[dp(10), dp(5)]
        )
        
        # Total odds row
        stats_grid.add_widget(Label(
            text='Parlay Odds:',
            halign='left',
            valign='middle',
            text_size=(None, dp(30))
        ))
        stats_grid.add_widget(Label(
            text=american_odds,
            halign='right',
            valign='middle',
            text_size=(None, dp(30)),
            bold=True
        ))
        
        # Probability row
        stats_grid.add_widget(Label(
            text='Win Probability:',
            halign='left',
            valign='middle',
            text_size=(None, dp(30))
        ))
        stats_grid.add_widget(Label(
            text=f"{combined_prob*100:.2f}%",
            halign='right',
            valign='middle',
            text_size=(None, dp(30))
        ))
        
        # Expected value row
        stats_grid.add_widget(Label(
            text='Expected Value:',
            halign='left',
            valign='middle',
            text_size=(None, dp(30))
        ))
        
        ev_color = get_color_from_hex('#4CAF50') if ev_percentage > 0 else get_color_from_hex('#F44336')
        stats_grid.add_widget(Label(
            text=f"{ev_percentage:.2f}%",
            halign='right',
            valign='middle',
            text_size=(None, dp(30)),
            color=ev_color
        ))
        
        content.add_widget(stats_grid)
        
        # Verdict label
        verdict_text = "This is a value parlay!" if ev_percentage > 0 else "This parlay does not have positive expected value."
        verdict_label = Label(
            text=verdict_text,
            size_hint=(1, None),
            height=dp(40),
            color=get_color_from_hex('#4CAF50') if ev_percentage > 0 else get_color_from_hex('#F44336')
        )
        content.add_widget(verdict_label)
        
        # Buttons
        buttons_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(10)
        )
        
        cancel_btn = Button(
            text='Cancel',
            size_hint=(0.5, 1),
            background_color=get_color_from_hex('#9E9E9E')
        )
        
        create_btn = Button(
            text='Create Parlay',
            size_hint=(0.5, 1),
            background_color=get_color_from_hex('#4CAF50') if ev_percentage > 0 else get_color_from_hex('#F44336')
        )
        
        # Create popup
        popup = Popup(
            title='Value Parlay Analysis',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        # Bind buttons
        cancel_btn.bind(on_press=popup.dismiss)
        create_btn.bind(on_press=lambda btn: self.create_actual_parlay(selected_bet_data, popup))
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(create_btn)
        content.add_widget(buttons_layout)
        
        # Open popup
        popup.open()
    
    def create_actual_parlay(self, bet_data_list, popup):
        """Create an actual parlay in the database."""
        try:
            # Get bet IDs
            bet_ids = [bet.get('bet_id') for bet in bet_data_list if bet.get('bet_id')]
            
            if not bet_ids or len(bet_ids) < 2:
                # Show error
                self.show_error_popup('Error', 'Could not create parlay: invalid bet IDs')
                return
            
            # Get bets from database
            bets = []
            for bet_id in bet_ids:
                bet = Bet.get_by_id(bet_id)
                if bet:
                    bets.append(bet)
            
            if len(bets) < 2:
                # Show error
                self.show_error_popup('Error', 'Could not create parlay: not enough valid bets')
                return
            
            # Calculate total stake based on bankroll
            try:
                bankroll = float(self.bankroll_input.text)
                stake = bankroll * 0.01  # Use 1% of bankroll for parlays
            except:
                stake = 10.0  # Default stake
            
            # Create parlay
            parlay = Parlay(bets=bets, stake=stake)
            
            # Calculate odds and payout
            parlay.calculate_odds()
            parlay.calculate_payout()
            
            # Set notes indicating this is a value parlay
            parlay.notes = "Value Parlay"
            
            # Save to database
            parlay.save()
            
            # Close popup
            popup.dismiss()
            
            # Show success popup
            success_popup = Popup(
                title='Success',
                content=Label(text='Value parlay created successfully!'),
                size_hint=(0.8, 0.4)
            )
            success_popup.open()
            
            # Clear selections
            self.selected_value_bets = []
            self.refresh_value_bets()
            
        except Exception as e:
            # Show error popup
            self.show_error_popup('Error', f'Failed to create parlay: {e}')
    
    def go_back(self, instance):
        """Go back to the previous screen."""
        self.save_settings()
        self.manager.current = 'main'
    
    def show_error_popup(self, title, message):
        """Show an error popup."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()