#!/usr/bin/env python3
"""
Bet Screens Module for BettingBuddy app.

Contains screens for bet management and detail views.
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
from ui.widgets import BetCard, FilterButton


class BetScreen(Screen):
    """Screen for displaying and managing bets."""
    
    current_filter = StringProperty("all")  # Filter: all, pending, won, lost
    current_sport = NumericProperty(None, allownone=True)  # Sport ID filter
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(title="Bets")
        self.layout.add_widget(self.header)
        
        # Filter buttons row
        self.filter_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            padding=[dp(10), dp(5)],
            spacing=dp(5)
        )
        
        # Status filter buttons
        self.all_filter = FilterButton(
            text="All",
            active=True,
            on_release=lambda x: self.set_filter("all")
        )
        
        self.pending_filter = FilterButton(
            text="Pending",
            active=False,
            on_release=lambda x: self.set_filter("pending")
        )
        
        self.won_filter = FilterButton(
            text="Won",
            active=False,
            on_release=lambda x: self.set_filter("won")
        )
        
        self.lost_filter = FilterButton(
            text="Lost",
            active=False,
            on_release=lambda x: self.set_filter("lost")
        )
        
        self.filter_row.add_widget(self.all_filter)
        self.filter_row.add_widget(self.pending_filter)
        self.filter_row.add_widget(self.won_filter)
        self.filter_row.add_widget(self.lost_filter)
        
        self.layout.add_widget(self.filter_row)
        
        # Sport filter dropdown button
        self.sport_filter_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), dp(5)],
            spacing=dp(10)
        )
        
        self.sport_label = Label(
            text="Sport:",
            size_hint_x=None,
            width=dp(50)
        )
        
        self.sport_dropdown = Button(
            text="All Sports",
            size_hint_x=0.7
        )
        self.sport_dropdown.bind(on_release=self.show_sport_popup)
        
        self.refresh_btn = Button(
            text="Refresh",
            size_hint_x=0.3
        )
        self.refresh_btn.bind(on_release=self.refresh_bets)
        
        self.sport_filter_row.add_widget(self.sport_label)
        self.sport_filter_row.add_widget(self.sport_dropdown)
        self.sport_filter_row.add_widget(self.refresh_btn)
        
        self.layout.add_widget(self.sport_filter_row)
        
        # Create bets list
        self.scroll_view = ScrollView()
        self.bets_list = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=[dp(10), dp(10)],
            size_hint_y=None
        )
        self.bets_list.bind(minimum_height=self.bets_list.setter("height"))
        self.scroll_view.add_widget(self.bets_list)
        
        self.layout.add_widget(self.scroll_view)
        
        # Navigation bar
        self.navbar = NavigationBar(active_button="bets")
        self.layout.add_widget(self.navbar)
        
        self.add_widget(self.layout)
    
    def on_pre_enter(self):
        """Load data before entering screen."""
        # Set navbar active button
        self.navbar.active_button = "bets"
        self.navbar.update_buttons()
        
        # Load bets
        self.load_bets()
    
    def load_bets(self):
        """Load bets based on current filters."""
        self.bets_list.clear_widgets()
        
        # Add loading indicator
        loading = Label(
            text="Loading bets...",
            size_hint_y=None,
            height=dp(40)
        )
        self.bets_list.add_widget(loading)
        
        # Schedule actual loading for next frame
        Clock.schedule_once(self._load_bets_data, 0.1)
    
    def _load_bets_data(self, dt):
        """Actual function to load bet data."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            self.bets_list.clear_widgets()
            self.bets_list.add_widget(Label(
                text="Could not connect to database",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Build query based on filters
        query = """
            SELECT b.*, t.name as team_name, s.name as sport_name, s.id as sport_id
            FROM bets b
            JOIN teams t ON b.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE 1=1
        """
        params = []
        
        # Apply status filter
        if self.current_filter != "all":
            query += " AND b.status = ?"
            params.append(self.current_filter)
        
        # Apply sport filter
        if self.current_sport is not None:
            query += " AND t.sport_id = ?"
            params.append(self.current_sport)
        
        # Order by event date
        query += " ORDER BY b.event_date DESC"
        
        # Execute query
        if params:
            db.execute(query, tuple(params))
        else:
            db.execute(query)
        
        bets = db.fetchall()
        
        # Clear and repopulate list
        self.bets_list.clear_widgets()
        
        if not bets:
            self.bets_list.add_widget(Label(
                text="No bets found with current filters",
                size_hint_y=None,
                height=dp(80)
            ))
            return
        
        # Add bet cards
        for bet in bets:
            bet_card = BetCard(bet=bet)
            bet_card.bind(on_release=lambda x, b=bet: self.show_bet_detail(b))
            self.bets_list.add_widget(bet_card)
    
    def set_filter(self, filter_type):
        """Set the status filter."""
        # Update filter state
        self.current_filter = filter_type
        
        # Update button states
        self.all_filter.active = (filter_type == "all")
        self.pending_filter.active = (filter_type == "pending")
        self.won_filter.active = (filter_type == "won")
        self.lost_filter.active = (filter_type == "lost")
        
        # Reload bets
        self.load_bets()
    
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
        """Set the sport filter."""
        self.current_sport = sport["id"]
        self.sport_dropdown.text = sport["name"]
        popup.dismiss()
        self.load_bets()
    
    def refresh_bets(self, instance=None):
        """Refresh the bets list."""
        self.load_bets()
    
    def show_bet_detail(self, bet):
        """Navigate to bet detail screen."""
        detail_screen = self.manager.get_screen("bet_detail")
        detail_screen.load_bet(bet["id"])
        self.manager.current = "bet_detail"


class BetDetailScreen(Screen):
    """Screen for viewing and updating bet details."""
    
    bet_id = NumericProperty(None, allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(
            title="Bet Details",
            show_back=True,
            back_screen="bets"
        )
        self.layout.add_widget(self.header)
        
        # Content area
        self.content = BoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(10)]
        )
        
        # Bet info section
        self.bet_info = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(280),
            spacing=dp(10)
        )
        
        # Team name
        self.team_label = Label(
            text="Team Name",
            font_size=dp(24),
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="middle",
            text_size=(dp(500), dp(40))
        )
        
        # Event details
        self.event_label = Label(
            text="vs Opponent",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            text_size=(dp(500), dp(30))
        )
        
        # Sport and Date
        self.details_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30)
        )
        
        self.sport_label = Label(
            text="Sport",
            size_hint_x=0.5,
            halign="left",
            valign="middle",
            text_size=(dp(250), dp(30))
        )
        
        self.date_label = Label(
            text="Date",
            size_hint_x=0.5,
            halign="right",
            valign="middle",
            text_size=(dp(250), dp(30))
        )
        
        self.details_box.add_widget(self.sport_label)
        self.details_box.add_widget(self.date_label)
        
        # Odds display
        self.odds_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            padding=[0, dp(10)]
        )
        
        self.odds_label = Label(
            text="Odds:",
            size_hint_x=0.3,
            halign="left",
            valign="middle",
            text_size=(dp(150), dp(40))
        )
        
        self.odds_value = Label(
            text="+100",
            font_size=dp(24),
            bold=True,
            size_hint_x=0.7,
            halign="right",
            valign="middle",
            text_size=(dp(350), dp(40))
        )
        
        self.odds_box.add_widget(self.odds_label)
        self.odds_box.add_widget(self.odds_value)
        
        # Status section
        self.status_label = Label(
            text="Status:",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            text_size=(dp(500), dp(30))
        )
        
        # Status buttons
        self.status_buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        self.pending_btn = Button(
            text="Pending",
            background_color=[0.3, 0.3, 0.3, 1]
        )
        self.pending_btn.bind(on_release=lambda x: self.update_status("pending"))
        
        self.won_btn = Button(
            text="Won",
            background_color=[0.2, 0.7, 0.2, 1]
        )
        self.won_btn.bind(on_release=lambda x: self.update_status("won"))
        
        self.lost_btn = Button(
            text="Lost",
            background_color=[0.7, 0.2, 0.2, 1]
        )
        self.lost_btn.bind(on_release=lambda x: self.update_status("lost"))
        
        self.status_buttons.add_widget(self.pending_btn)
        self.status_buttons.add_widget(self.won_btn)
        self.status_buttons.add_widget(self.lost_btn)
        
        # Add to parlay button
        self.add_to_parlay_btn = Button(
            text="Add to Parlay",
            size_hint_y=None,
            height=dp(50),
            background_color=[0.2, 0.5, 0.9, 1]
        )
        self.add_to_parlay_btn.bind(on_release=self.add_to_parlay)
        
        # Add all widgets to info section
        self.bet_info.add_widget(self.team_label)
        self.bet_info.add_widget(self.event_label)
        self.bet_info.add_widget(self.details_box)
        self.bet_info.add_widget(self.odds_box)
        self.bet_info.add_widget(self.status_label)
        self.bet_info.add_widget(self.status_buttons)
        self.bet_info.add_widget(self.add_to_parlay_btn)
        
        # Add info section to content
        self.content.add_widget(self.bet_info)
        
        # Add content to layout
        self.layout.add_widget(self.content)
        
        self.add_widget(self.layout)
    
    def load_bet(self, bet_id):
        """Load bet data."""
        self.bet_id = bet_id
        
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Get bet data
        bet = db.get_bet_by_id(bet_id)
        
        if not bet:
            return
        
        # Update UI with bet data
        self.team_label.text = bet.get("team_name", "Unknown Team")
        self.event_label.text = bet.get("description", "")
        self.sport_label.text = bet.get("sport_name", "Unknown Sport")
        
        # Format date
        event_date = bet.get("event_date")
        if event_date:
            try:
                # Try to parse date
                date_obj = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
                self.date_label.text = formatted_date
            except (ValueError, AttributeError):
                self.date_label.text = event_date
        else:
            self.date_label.text = "No date"
        
        # Display odds in user's preferred format
        odds_str = bet.get("odds", "+100")
        self.odds_value.text = app.convert_odds(odds_str)
        
        # Update status section
        status = bet.get("status", "pending")
        self.status_label.text = f"Status: {status.capitalize()}"
        
        # Highlight active status button
        self.pending_btn.background_color = [0.3, 0.3, 0.3, 1]
        self.won_btn.background_color = [0.2, 0.7, 0.2, 1]
        self.lost_btn.background_color = [0.7, 0.2, 0.2, 1]
        
        if status == "pending":
            self.pending_btn.background_color = [0.5, 0.5, 0.5, 1]
            self.add_to_parlay_btn.disabled = False
        elif status == "won":
            self.won_btn.background_color = [0.4, 0.9, 0.4, 1]
            self.add_to_parlay_btn.disabled = True
        elif status == "lost":
            self.lost_btn.background_color = [0.9, 0.4, 0.4, 1]
            self.add_to_parlay_btn.disabled = True
    
    def update_status(self, status):
        """Update bet status."""
        if self.bet_id is None:
            return
        
        app = self.manager.parent
        db = app.db
        
        if not db:
            return
        
        # Update status in database
        success = db.update_bet_status(self.bet_id, status)
        
        if success:
            # Reload bet data
            self.load_bet(self.bet_id)
            
            # Show success message
            self.show_message("Status Updated", f"Bet status updated to {status.capitalize()}")
        else:
            # Show error message
            self.show_message("Error", "Failed to update bet status")
    
    def add_to_parlay(self, instance):
        """Add bet to a new or existing parlay."""
        # Navigate to parlay detail screen with this bet
        detail_screen = self.manager.get_screen("parlay_detail")
        detail_screen.clear_form()
        
        # Get the bet and add it
        app = self.manager.parent
        db = app.db
        bet = db.get_bet_by_id(self.bet_id)
        
        if bet:
            detail_screen.bet_ids = [self.bet_id]
            detail_screen.bets_list.clear_widgets()
            
            # Add bet card
            from ui.widgets import BetCard
            bet_card = BetCard(bet=bet, in_parlay=True)
            bet_card.remove_callback = lambda: detail_screen.remove_bet(self.bet_id)
            detail_screen.bets_list.add_widget(bet_card)
            
            # Calculate odds
            detail_screen.calculate_totals()
            
            # Navigate to screen
            self.manager.current = "parlay_detail"
    
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
