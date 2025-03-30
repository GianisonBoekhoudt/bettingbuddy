#!/usr/bin/env python3
"""
Parlay Screens Module for BettingBuddy app.

Contains screens for parlay management and recommendations.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock

from datetime import datetime

from ui.screens import HeaderBar, NavigationBar
from ui.widgets import BetCard, ParlayCard, RecommendationCard


class ParlayScreen(Screen):
    """Screen for displaying parlays and recommendations."""
    
    active_tab = StringProperty("my_parlays")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(title="Parlays")
        self.layout.add_widget(self.header)
        
        # Tab buttons
        self.tabs = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(2)
        )
        
        self.my_parlays_btn = Button(
            text="My Parlays",
            on_release=lambda x: self.switch_tab("my_parlays")
        )
        
        self.recommendations_btn = Button(
            text="Recommendations",
            on_release=lambda x: self.switch_tab("recommendations")
        )
        
        self.tabs.add_widget(self.my_parlays_btn)
        self.tabs.add_widget(self.recommendations_btn)
        self.layout.add_widget(self.tabs)
        
        # Content area
        self.content = BoxLayout(orientation="vertical")
        
        # My Parlays content
        self.my_parlays_content = BoxLayout(orientation="vertical")
        
        # Add new parlay button
        self.new_parlay_btn = Button(
            text="Create New Parlay",
            size_hint_y=None,
            height=dp(50)
        )
        self.new_parlay_btn.bind(on_release=self.create_new_parlay)
        self.my_parlays_content.add_widget(self.new_parlay_btn)
        
        # Parlays list
        self.parlays_scroll = ScrollView()
        self.parlays_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )
        self.parlays_list.bind(minimum_height=self.parlays_list.setter("height"))
        self.parlays_scroll.add_widget(self.parlays_list)
        self.my_parlays_content.add_widget(self.parlays_scroll)
        
        # Recommendations content
        self.recommendations_content = BoxLayout(orientation="vertical")
        
        # Sport filter dropdown
        self.filter_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            padding=[dp(10), dp(5)],
            spacing=dp(10)
        )
        
        self.filter_label = Label(
            text="Sport:",
            size_hint_x=None,
            width=dp(50)
        )
        
        self.sport_filter = Button(
            text="All Sports",
            size_hint_x=1
        )
        self.sport_filter.bind(on_release=self.show_sport_popup)
        
        self.refresh_btn = Button(
            text="Refresh",
            size_hint_x=None,
            width=dp(80)
        )
        self.refresh_btn.bind(on_release=self.refresh_recommendations)
        
        self.filter_layout.add_widget(self.filter_label)
        self.filter_layout.add_widget(self.sport_filter)
        self.filter_layout.add_widget(self.refresh_btn)
        self.recommendations_content.add_widget(self.filter_layout)
        
        # Recommendations scroll view
        self.recommendations_scroll = ScrollView()
        self.recommendations_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )
        self.recommendations_list.bind(minimum_height=self.recommendations_list.setter("height"))
        self.recommendations_scroll.add_widget(self.recommendations_list)
        self.recommendations_content.add_widget(self.recommendations_scroll)
        
        # Navigation bar
        self.navbar = NavigationBar(active_button="parlays")
        
        # Add content to layout based on active tab
        self.update_content()
        self.layout.add_widget(self.content)
        self.layout.add_widget(self.navbar)
        
        self.add_widget(self.layout)
    
    def on_pre_enter(self):
        """Load data before entering screen."""
        # Set navbar active button
        self.navbar.active_button = "parlays"
        self.navbar.update_buttons()
        
        # Refresh data
        self.load_parlays()
        self.load_recommendations()
    
    def switch_tab(self, tab):
        """Switch between tabs."""
        self.active_tab = tab
        self.update_content()
    
    def update_content(self):
        """Update content based on active tab."""
        self.content.clear_widgets()
        
        if self.active_tab == "my_parlays":
            self.my_parlays_btn.background_color = self.app.dark_primary_color
            self.recommendations_btn.background_color = self.app.primary_color
            self.content.add_widget(self.my_parlays_content)
        else:
            self.my_parlays_btn.background_color = self.app.primary_color
            self.recommendations_btn.background_color = self.app.dark_primary_color
            self.content.add_widget(self.recommendations_content)
    
    def load_parlays(self):
        """Load user's parlays from database."""
        self.parlays_list.clear_widgets()
        
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Get all parlays
        parlays = db.get_all_parlays()
        
        if not parlays:
            no_parlays = Label(
                text="No parlays found. Create a new parlay to get started.",
                size_hint_y=None,
                height=dp(100)
            )
            self.parlays_list.add_widget(no_parlays)
            return
        
        # Add parlays to the list
        for parlay in parlays:
            parlay_card = ParlayCard(parlay=parlay)
            parlay_card.bind(on_release=lambda x, p=parlay: self.show_parlay_detail(p))
            self.parlays_list.add_widget(parlay_card)
    
    def load_recommendations(self):
        """Load parlay recommendations."""
        self.recommendations_list.clear_widgets()
        
        app = self.manager.parent
        db = app.db
        recommender = app.parlay_recommender
        
        if not db or not recommender:
            return
        
        # Get active bets for recommendations
        active_bets = []
        query = """
        SELECT b.id as bet_id, b.team_id, b.odds, b.description, b.event_date,
               t.name as team_name, s.name as sport_name, s.id as sport_id
        FROM bets b
        JOIN teams t ON b.team_id = t.id
        JOIN sports s ON t.sport_id = s.id
        WHERE b.status = 'pending'
        """
        db.execute(query)
        for row in db.fetchall():
            active_bets.append(row)
        
        if not active_bets:
            self.recommendations_list.add_widget(Label(
                text="No active bets found for recommendations.\nAdd some bets first.",
                size_hint_y=None,
                height=dp(100)
            ))
            return
        
        # Get recommendations
        all_recs = recommender.get_all_recommendations(active_bets)
        
        # Display recommendations by category
        categories = [
            ("Recommended Single Bets", all_recs.get('single_bets', [])),
            ("2-Leg Parlay Recommendations", all_recs.get('two_leg_parlays', [])),
            ("3-Leg Parlay Recommendations", all_recs.get('three_leg_parlays', [])),
            ("Favorite Parlay Recommendations", all_recs.get('favorite_parlays', []))
        ]
        
        for category_title, recs in categories:
            if recs:
                # Add category header
                self.recommendations_list.add_widget(Label(
                    text=category_title,
                    size_hint_y=None,
                    height=dp(40),
                    font_size=dp(16),
                    bold=True
                ))
                
                # Add recommendations
                for rec in recs:
                    rec_card = RecommendationCard(recommendation=rec)
                    rec_card.bind(on_release=lambda x, r=rec: self.create_from_recommendation(r))
                    self.recommendations_list.add_widget(rec_card)
            
        if all(not recs for _, recs in categories):
            self.recommendations_list.add_widget(Label(
                text="No recommendations available.\nTry selecting a different sport.",
                size_hint_y=None,
                height=dp(100)
            ))
    
    def show_sport_popup(self, instance):
        """Show popup for selecting sport filter."""
        app = self.manager.parent
        db = app.db
        
        # Get sports
        sports = [{"id": None, "name": "All Sports"}]
        if db:
            sports.extend(db.get_sports())
        
        # Create content
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # Add buttons for each sport
        for sport in sports:
            btn = Button(
                text=sport["name"],
                size_hint_y=None,
                height=dp(40)
            )
            btn.bind(on_release=lambda x, s=sport: self.set_sport_filter(popup, s))
            content.add_widget(btn)
        
        # Create popup
        popup = Popup(
            title="Select Sport",
            content=content,
            size_hint=(0.8, 0.9)
        )
        popup.open()
    
    def set_sport_filter(self, popup, sport):
        """Set the sport filter and refresh recommendations."""
        app = self.manager.parent
        app.current_sport_filter = sport["id"]
        self.sport_filter.text = sport["name"]
        popup.dismiss()
        self.refresh_recommendations()
    
    def refresh_recommendations(self, instance=None):
        """Refresh recommendations list."""
        # Display loading indicator
        self.recommendations_list.clear_widgets()
        loading = Label(
            text="Loading recommendations...",
            size_hint_y=None,
            height=dp(100)
        )
        self.recommendations_list.add_widget(loading)
        
        # Schedule actual load for next frame
        Clock.schedule_once(lambda dt: self.load_recommendations(), 0.1)
    
    def create_new_parlay(self, instance):
        """Create a new empty parlay."""
        self.manager.current = "parlay_detail"
    
    def show_parlay_detail(self, parlay):
        """Show parlay details screen."""
        detail_screen = self.manager.get_screen("parlay_detail")
        detail_screen.load_parlay(parlay["id"])
        self.manager.current = "parlay_detail"
    
    def create_from_recommendation(self, recommendation):
        """Create a new parlay from a recommendation."""
        detail_screen = self.manager.get_screen("parlay_detail")
        detail_screen.load_from_recommendation(recommendation)
        self.manager.current = "parlay_detail"
    
    @property
    def app(self):
        """Get the app instance."""
        return self.manager.parent


class ParlayDetailScreen(Screen):
    """Screen for creating and editing parlays."""
    
    parlay_id = NumericProperty(None, allownone=True)
    total_odds = StringProperty("0.00")
    potential_payout = StringProperty("$0.00")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.bet_ids = []  # List of bet IDs in the parlay
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(
            title="Parlay Details",
            show_back=True,
            back_screen="parlays"
        )
        self.layout.add_widget(self.header)
        
        # Content area
        self.content = BoxLayout(
            orientation="vertical",
            padding=[dp(10), dp(5)]
        )
        
        # Parlay info section
        self.info_section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=[0, dp(10)]
        )
        
        # Stake input row
        self.stake_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40)
        )
        
        self.stake_label = Label(
            text="Stake ($):",
            size_hint_x=None,
            width=dp(100)
        )
        
        self.stake_input = TextInput(
            text="10.00",
            input_filter="float",
            multiline=False,
            size_hint_x=1
        )
        self.stake_input.bind(text=self.update_potential_payout)
        
        self.stake_row.add_widget(self.stake_label)
        self.stake_row.add_widget(self.stake_input)
        
        # Odds and payout row
        self.odds_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40)
        )
        
        self.odds_label = Label(
            text="Total Odds:",
            size_hint_x=None,
            width=dp(100)
        )
        
        self.odds_value = Label(
            text=self.total_odds,
            size_hint_x=1,
            halign="left"
        )
        
        self.odds_row.add_widget(self.odds_label)
        self.odds_row.add_widget(self.odds_value)
        
        # Potential payout row
        self.payout_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40)
        )
        
        self.payout_label = Label(
            text="Payout:",
            size_hint_x=None,
            width=dp(100)
        )
        
        self.payout_value = Label(
            text=self.potential_payout,
            size_hint_x=1,
            halign="left"
        )
        
        self.payout_row.add_widget(self.payout_label)
        self.payout_row.add_widget(self.payout_value)
        
        self.info_section.add_widget(self.stake_row)
        self.info_section.add_widget(self.odds_row)
        self.info_section.add_widget(self.payout_row)
        
        # Bets section
        self.bets_label = Label(
            text="Bets in This Parlay",
            size_hint_y=None,
            height=dp(30),
            halign="left"
        )
        
        self.bets_scroll = ScrollView()
        self.bets_list = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )
        self.bets_list.bind(minimum_height=self.bets_list.setter("height"))
        self.bets_scroll.add_widget(self.bets_list)
        
        # Add bet button
        self.add_bet_btn = Button(
            text="Add Bet to Parlay",
            size_hint_y=None,
            height=dp(50)
        )
        self.add_bet_btn.bind(on_release=self.show_add_bet_popup)
        
        # Notes section
        self.notes_label = Label(
            text="Notes",
            size_hint_y=None,
            height=dp(30),
            halign="left"
        )
        
        self.notes_input = TextInput(
            hint_text="Add notes about this parlay",
            size_hint_y=None,
            height=dp(100),
            multiline=True
        )
        
        # Save/delete buttons
        self.button_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10),
            padding=[0, dp(10)]
        )
        
        self.save_btn = Button(
            text="Save Parlay",
            size_hint_x=0.7
        )
        self.save_btn.bind(on_release=self.save_parlay)
        
        self.delete_btn = Button(
            text="Delete",
            size_hint_x=0.3
        )
        self.delete_btn.bind(on_release=self.confirm_delete)
        
        self.button_row.add_widget(self.save_btn)
        self.button_row.add_widget(self.delete_btn)
        
        # Add all sections to content
        self.content.add_widget(self.info_section)
        self.content.add_widget(self.bets_label)
        self.content.add_widget(self.bets_scroll)
        self.content.add_widget(self.add_bet_btn)
        self.content.add_widget(self.notes_label)
        self.content.add_widget(self.notes_input)
        self.content.add_widget(self.button_row)
        
        self.layout.add_widget(self.content)
        
        self.add_widget(self.layout)
    
    def on_pre_enter(self):
        """Prepare the screen before entering."""
        # If no parlay_id, we're creating a new parlay
        if self.parlay_id is None:
            self.header.title = "New Parlay"
            self.delete_btn.disabled = True
            self.clear_form()
        else:
            self.header.title = "Edit Parlay"
            self.delete_btn.disabled = False
    
    def clear_form(self):
        """Clear the form for a new parlay."""
        self.bet_ids = []
        self.stake_input.text = "10.00"
        self.notes_input.text = ""
        self.total_odds = "0.00"
        self.potential_payout = "$0.00"
        self.bets_list.clear_widgets()
        self.update_odds_display()
    
    def load_parlay(self, parlay_id):
        """Load parlay data."""
        self.parlay_id = parlay_id
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Get parlay data
        parlay = db.get_parlay_by_id(parlay_id)
        
        if not parlay:
            return
        
        # Populate form
        self.stake_input.text = str(parlay["stake"])
        self.notes_input.text = parlay["notes"] or ""
        
        # Store bets
        self.bet_ids = []
        self.bets_list.clear_widgets()
        
        if "bets" in parlay:
            for bet in parlay["bets"]:
                self.bet_ids.append(bet["id"])
                
                # Add bet card
                bet_card = BetCard(bet=bet, in_parlay=True)
                bet_card.remove_callback = lambda bid=bet["id"]: self.remove_bet(bid)
                self.bets_list.add_widget(bet_card)
        
        # Calculate odds and payout
        self.calculate_totals()
    
    def load_from_recommendation(self, recommendation):
        """Load parlay from a recommendation."""
        self.clear_form()
        self.parlay_id = None
        self.header.title = "New Parlay from Recommendation"
        
        # Add bets from recommendation
        self.bet_ids = []
        self.bets_list.clear_widgets()
        
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        if "bets" in recommendation:
            for rec_bet in recommendation["bets"]:
                bet_id = rec_bet.get("bet_id") or rec_bet.get("id")
                if bet_id:
                    self.bet_ids.append(bet_id)
                    
                    # Get full bet data
                    bet = db.get_bet_by_id(bet_id)
                    
                    if bet:
                        # Add bet card
                        bet_card = BetCard(bet=bet, in_parlay=True)
                        bet_card.remove_callback = lambda bid=bet["id"]: self.remove_bet(bid)
                        self.bets_list.add_widget(bet_card)
        
        # Set American odds 
        if "american_odds" in recommendation:
            self.american_odds = recommendation["american_odds"]
        
        # Calculate odds and payout
        self.calculate_totals()
    
    def update_odds_display(self):
        """Update the odds display."""
        app = self.manager.parent
        odds_format = app.odds_format
        
        # Calculate decimal odds
        decimal_odds = 1.0
        for bet_id in self.bet_ids:
            bet = app.db.get_bet_by_id(bet_id)
            if bet:
                # Convert to decimal format
                odds_str = bet["odds"]
                if odds_str.startswith('+'):
                    american_odds = int(odds_str[1:])
                    decimal = (american_odds / 100) + 1
                else:
                    american_odds = int(odds_str[1:])
                    decimal = (100 / american_odds) + 1
                
                decimal_odds *= decimal
        
        # Format based on user preference
        if odds_format == 'decimal':
            self.total_odds = f"{decimal_odds:.2f}"
        elif odds_format == 'american':
            if decimal_odds > 2.0:
                american = f"+{int((decimal_odds - 1) * 100)}"
            else:
                american = f"-{int(100 / (decimal_odds - 1))}"
            self.total_odds = american
        elif odds_format == 'fractional':
            # Simplified conversion to fractional
            decimal_minus_one = decimal_odds - 1
            if decimal_minus_one.is_integer():
                self.total_odds = f"{int(decimal_minus_one)}/1"
            else:
                # Approximation for display
                self.total_odds = f"{decimal_minus_one:.2f}/1"
        
        # Update label
        self.odds_value.text = self.total_odds
    
    def update_potential_payout(self, instance=None, value=None):
        """Update potential payout when stake changes."""
        try:
            stake = float(self.stake_input.text or 0)
            
            # Calculate decimal odds
            decimal_odds = 1.0
            for bet_id in self.bet_ids:
                bet = self.app.db.get_bet_by_id(bet_id)
                if bet:
                    # Convert to decimal format
                    odds_str = bet["odds"]
                    if odds_str.startswith('+'):
                        american_odds = int(odds_str[1:])
                        decimal = (american_odds / 100) + 1
                    else:
                        american_odds = int(odds_str[1:])
                        decimal = (100 / american_odds) + 1
                    
                    decimal_odds *= decimal
            
            # Calculate payout
            payout = stake * decimal_odds
            self.potential_payout = f"${payout:.2f}"
            self.payout_value.text = self.potential_payout
            
        except (ValueError, ZeroDivisionError):
            self.potential_payout = "$0.00"
            self.payout_value.text = self.potential_payout
    
    def calculate_totals(self):
        """Calculate total odds and potential payout."""
        self.update_odds_display()
        self.update_potential_payout()
    
    def show_add_bet_popup(self, instance):
        """Show popup for adding a bet to the parlay."""
        app = self.manager.parent
        db = app.db
        
        # Get active bets not already in the parlay
        query = """
        SELECT b.id, b.team_id, b.odds, b.description, b.event_date,
               t.name as team_name, s.name as sport_name
        FROM bets b
        JOIN teams t ON b.team_id = t.id
        JOIN sports s ON t.sport_id = s.id
        WHERE b.status = 'pending'
        """
        db.execute(query)
        all_bets = db.fetchall()
        
        # Filter out bets already in the parlay
        available_bets = [bet for bet in all_bets if bet["id"] not in self.bet_ids]
        
        # Create content
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        if not available_bets:
            content.add_widget(Label(text="No available bets to add."))
            
            close_btn = Button(
                text="Close",
                size_hint_y=None,
                height=dp(40)
            )
            content.add_widget(close_btn)
            
            popup = Popup(
                title="Add Bet to Parlay",
                content=content,
                size_hint=(0.9, 0.5)
            )
            
            close_btn.bind(on_release=popup.dismiss)
            popup.open()
            return
        
        # Scroll view for bets
        scroll = ScrollView()
        bet_list = GridLayout(cols=1, spacing=5, size_hint_y=None)
        bet_list.bind(minimum_height=bet_list.setter("height"))
        
        for bet in available_bets:
            # Create bet card
            bet_card = BetCard(bet=bet, selectable=True)
            bet_card.height = dp(80)
            bet_card.size_hint_y = None
            
            # Bind to add bet
            bet_card.bind(on_release=lambda x, b=bet: self.add_bet_to_parlay(popup, b))
            
            bet_list.add_widget(bet_card)
        
        scroll.add_widget(bet_list)
        content.add_widget(scroll)
        
        # Create popup
        popup = Popup(
            title="Add Bet to Parlay",
            content=content,
            size_hint=(0.9, 0.9)
        )
        popup.open()
    
    def add_bet_to_parlay(self, popup, bet):
        """Add a bet to the parlay."""
        popup.dismiss()
        
        # Add the bet if not already in the parlay
        if bet["id"] not in self.bet_ids:
            self.bet_ids.append(bet["id"])
            
            # Add bet card
            bet_card = BetCard(bet=bet, in_parlay=True)
            bet_card.remove_callback = lambda: self.remove_bet(bet["id"])
            self.bets_list.add_widget(bet_card)
            
            # Recalculate totals
            self.calculate_totals()
    
    def remove_bet(self, bet_id):
        """Remove a bet from the parlay."""
        if bet_id in self.bet_ids:
            self.bet_ids.remove(bet_id)
            
            # Remove bet card
            for child in self.bets_list.children:
                if hasattr(child, 'bet') and child.bet["id"] == bet_id:
                    self.bets_list.remove_widget(child)
                    break
            
            # Recalculate totals
            self.calculate_totals()
    
    def save_parlay(self, instance):
        """Save the parlay to the database."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Check if we have bets
        if not self.bet_ids:
            self.show_message("Error", "A parlay must contain at least one bet.")
            return
        
        # Get form values
        try:
            stake = float(self.stake_input.text or 0)
            if stake <= 0:
                self.show_message("Error", "Stake must be greater than zero.")
                return
        except ValueError:
            self.show_message("Error", "Invalid stake amount.")
            return
        
        notes = self.notes_input.text
        
        # Calculate decimal odds for storage
        decimal_odds = 1.0
        for bet_id in self.bet_ids:
            bet = app.db.get_bet_by_id(bet_id)
            if bet:
                # Convert to decimal format
                odds_str = bet["odds"]
                if odds_str.startswith('+'):
                    american_odds = int(odds_str[1:])
                    decimal = (american_odds / 100) + 1
                else:
                    american_odds = int(odds_str[1:])
                    decimal = (100 / american_odds) + 1
                
                decimal_odds *= decimal
        
        # Convert to American format for storage
        if decimal_odds > 2.0:
            american_odds = f"+{int((decimal_odds - 1) * 100)}"
        else:
            american_odds = f"-{int(100 / (decimal_odds - 1))}"
        
        # Calculate potential payout
        potential_payout = stake * decimal_odds
        
        # Save to database
        if self.parlay_id is None:
            # Create new parlay
            parlay_id = db.create_parlay(
                self.bet_ids,
                stake,
                american_odds,
                potential_payout,
                notes
            )
            
            if parlay_id:
                self.show_message("Success", "Parlay created successfully.")
                self.manager.current = "parlays"
            else:
                self.show_message("Error", "Failed to create parlay.")
        else:
            # Update existing parlay - need to delete and recreate
            # Delete existing parlay
            db.execute("DELETE FROM parlay_bets WHERE parlay_id = ?", (self.parlay_id,))
            
            # Update parlay details
            db.execute(
                """
                UPDATE parlays 
                SET stake = ?, total_odds = ?, potential_payout = ?, notes = ?
                WHERE id = ?
                """,
                (stake, american_odds, potential_payout, notes, self.parlay_id)
            )
            
            # Add bets to parlay
            for bet_id in self.bet_ids:
                db.execute(
                    "INSERT INTO parlay_bets (parlay_id, bet_id) VALUES (?, ?)",
                    (self.parlay_id, bet_id)
                )
            
            db.commit()
            self.show_message("Success", "Parlay updated successfully.")
            self.manager.current = "parlays"
    
    def confirm_delete(self, instance):
        """Confirm parlay deletion."""
        if self.parlay_id is None:
            # Nothing to delete
            self.manager.current = "parlays"
            return
        
        # Create confirmation popup
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        message = Label(
            text="Are you sure you want to delete this parlay?",
            size_hint_y=None,
            height=dp(50)
        )
        
        button_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=10
        )
        
        cancel_btn = Button(text="Cancel")
        delete_btn = Button(text="Delete")
        
        button_row.add_widget(cancel_btn)
        button_row.add_widget(delete_btn)
        
        content.add_widget(message)
        content.add_widget(button_row)
        
        popup = Popup(
            title="Confirm Deletion",
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        cancel_btn.bind(on_release=popup.dismiss)
        delete_btn.bind(on_release=lambda x: self.delete_parlay(popup))
        
        popup.open()
    
    def delete_parlay(self, popup):
        """Delete the parlay."""
        popup.dismiss()
        
        app = self.manager.parent
        db = app.db
        
        if not db or self.parlay_id is None:
            return
        
        # Delete parlay
        db.execute("DELETE FROM parlay_bets WHERE parlay_id = ?", (self.parlay_id,))
        db.execute("DELETE FROM parlays WHERE id = ?", (self.parlay_id,))
        db.commit()
        
        self.show_message("Success", "Parlay deleted successfully.")
        self.manager.current = "parlays"
    
    def show_message(self, title, message):
        """Show a message popup."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        msg_label = Label(
            text=message,
            size_hint_y=None,
            height=dp(50)
        )
        
        close_btn = Button(
            text="OK",
            size_hint_y=None,
            height=dp(50)
        )
        
        content.add_widget(msg_label)
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        close_btn.bind(on_release=popup.dismiss)
        popup.open()
    
    @property
    def app(self):
        """Get the app instance."""
        return self.manager.parent
