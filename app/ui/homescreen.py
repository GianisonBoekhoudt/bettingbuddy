#!/usr/bin/env python3
"""
HomeScreen Module for BettingBuddy app.

Implements the main dashboard screen.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock

from datetime import datetime, timedelta
import pytz

from ui.screens import HeaderBar, NavigationBar
from ui.widgets import BetCard, ParlayCard, SummaryCard


class HomeScreen(Screen):
    """Main dashboard screen showing betting overview and recommendations."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Main layout
        self.layout = BoxLayout(orientation="vertical")
        
        # Add header
        self.header = HeaderBar(title="BettingBuddy")
        self.layout.add_widget(self.header)
        
        # Scrollable content
        self.scroll_view = ScrollView()
        self.content = GridLayout(
            cols=1,
            spacing=dp(15),
            padding=[dp(10), dp(10)],
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        
        # Summary cards section
        self.summary_section = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(100)
        )
        
        # Pending bets card
        self.pending_card = SummaryCard(
            title="Pending Bets",
            value="0",
            icon="calendar-check"
        )
        
        # Active parlays card
        self.parlays_card = SummaryCard(
            title="Active Parlays",
            value="0",
            icon="layers"
        )
        
        # Recent results card
        self.results_card = SummaryCard(
            title="Win Rate",
            value="0%",
            icon="trending-up"
        )
        
        self.summary_section.add_widget(self.pending_card)
        self.summary_section.add_widget(self.parlays_card)
        self.summary_section.add_widget(self.results_card)
        
        self.content.add_widget(self.summary_section)
        
        # Upcoming events section
        self.upcoming_label = Label(
            text="Today's Events",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            halign="left",
            valign="middle",
            text_size=(dp(400), dp(40))
        )
        self.content.add_widget(self.upcoming_label)
        
        # Placeholder for upcoming events
        self.upcoming_events = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )
        self.upcoming_events.bind(minimum_height=self.upcoming_events.setter("height"))
        self.content.add_widget(self.upcoming_events)
        
        # Top recommendations section
        self.recommendations_label = Label(
            text="Recommended Bets",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            halign="left",
            valign="middle",
            text_size=(dp(400), dp(40))
        )
        self.content.add_widget(self.recommendations_label)
        
        # Placeholder for recommendations
        self.recommendations = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )
        self.recommendations.bind(minimum_height=self.recommendations.setter("height"))
        self.content.add_widget(self.recommendations)
        
        # Recent parlays section
        self.parlays_label = Label(
            text="Recent Parlays",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            halign="left",
            valign="middle",
            text_size=(dp(400), dp(40))
        )
        self.content.add_widget(self.parlays_label)
        
        # Placeholder for recent parlays
        self.recent_parlays = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None
        )
        self.recent_parlays.bind(minimum_height=self.recent_parlays.setter("height"))
        self.content.add_widget(self.recent_parlays)
        
        # Add scroll view to layout
        self.scroll_view.add_widget(self.content)
        self.layout.add_widget(self.scroll_view)
        
        # Navigation bar
        self.navbar = NavigationBar(active_button="home")
        self.layout.add_widget(self.navbar)
        
        self.add_widget(self.layout)
    
    def on_pre_enter(self):
        """Load data before entering the screen."""
        # Set navbar active button
        self.navbar.active_button = "home"
        self.navbar.update_buttons()
        
        # Load all data
        self.load_data()
    
    def load_data(self):
        """Load all dashboard data."""
        # Show loading state
        self.clear_sections()
        self.upcoming_events.add_widget(Label(
            text="Loading today's events...",
            size_hint_y=None,
            height=dp(40)
        ))
        self.recommendations.add_widget(Label(
            text="Loading recommendations...",
            size_hint_y=None,
            height=dp(40)
        ))
        self.recent_parlays.add_widget(Label(
            text="Loading recent parlays...",
            size_hint_y=None,
            height=dp(40)
        ))
        
        # Schedule actual loading for next frame
        Clock.schedule_once(self.load_dashboard_data, 0.1)
    
    def clear_sections(self):
        """Clear all content sections."""
        self.upcoming_events.clear_widgets()
        self.recommendations.clear_widgets()
        self.recent_parlays.clear_widgets()
    
    def load_dashboard_data(self, dt):
        """Load all dashboard data from database."""
        app = self.manager.parent
        db = app.db
        
        if not db:
            self.show_connection_error()
            return
        
        # Clear all sections
        self.clear_sections()
        
        # Load summary stats
        self.load_summary_stats()
        
        # Load today's events
        self.load_upcoming_events()
        
        # Load recommendations
        self.load_recommendations()
        
        # Load recent parlays
        self.load_recent_parlays()
    
    def show_connection_error(self):
        """Show connection error message."""
        for section in [self.upcoming_events, self.recommendations, self.recent_parlays]:
            section.add_widget(Label(
                text="Could not connect to database. Please restart the app.",
                size_hint_y=None,
                height=dp(40)
            ))
    
    def load_summary_stats(self):
        """Load and display summary statistics."""
        app = self.manager.parent
        db = app.db
        
        # Get pending bets count
        db.execute("SELECT COUNT(*) as count FROM bets WHERE status = 'pending'")
        pending_count = db.fetchone()["count"]
        self.pending_card.value = str(pending_count)
        
        # Get active parlays count
        db.execute("SELECT COUNT(*) as count FROM parlays WHERE status = 'pending'")
        parlays_count = db.fetchone()["count"]
        self.parlays_card.value = str(parlays_count)
        
        # Calculate win rate
        db.execute("""
            SELECT 
                SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM bets
            WHERE status IN ('won', 'lost')
        """)
        result = db.fetchone()
        
        if result and result["total"] > 0:
            win_rate = (result["wins"] / result["total"]) * 100
            self.results_card.value = f"{win_rate:.1f}%"
        else:
            self.results_card.value = "N/A"
    
    def load_upcoming_events(self):
        """Load today's upcoming events."""
        app = self.manager.parent
        db = app.db
        
        # Calculate today's date range
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Format for SQLite
        today_start_str = today_start.strftime("%Y-%m-%d %H:%M:%S")
        today_end_str = today_end.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get today's events
        db.execute("""
            SELECT b.*, t.name as team_name, s.name as sport_name
            FROM bets b
            JOIN teams t ON b.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE b.status = 'pending'
            AND b.event_date BETWEEN ? AND ?
            ORDER BY b.event_date
            LIMIT 5
        """, (today_start_str, today_end_str))
        
        today_events = db.fetchall()
        
        if not today_events:
            self.upcoming_events.add_widget(Label(
                text="No events scheduled for today",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Add events to the list
        for event in today_events:
            bet_card = BetCard(bet=event)
            bet_card.bind(on_release=lambda x, e=event: self.show_bet_detail(e))
            self.upcoming_events.add_widget(bet_card)
        
        # Add "View All" button
        view_all = Button(
            text="View All Events",
            size_hint_y=None,
            height=dp(40)
        )
        view_all.bind(on_release=self.go_to_bets)
        self.upcoming_events.add_widget(view_all)
    
    def load_recommendations(self):
        """Load bet recommendations."""
        app = self.manager.parent
        db = app.db
        recommender = app.parlay_recommender
        
        if not recommender:
            self.recommendations.add_widget(Label(
                text="Recommendations engine not available",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Get active bets for recommendations
        db.execute("""
            SELECT b.id as bet_id, b.team_id, b.odds, b.description, b.event_date,
                   t.name as team_name, s.name as sport_name, s.id as sport_id
            FROM bets b
            JOIN teams t ON b.team_id = t.id
            JOIN sports s ON t.sport_id = s.id
            WHERE b.status = 'pending'
        """)
        
        active_bets = db.fetchall()
        
        if not active_bets:
            self.recommendations.add_widget(Label(
                text="No active bets available for recommendations",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Get recommendations
        all_recs = recommender.get_all_recommendations(active_bets)
        
        # Display single bet recommendations
        single_bets = all_recs.get('single_bets', [])
        
        if not single_bets:
            self.recommendations.add_widget(Label(
                text="No recommendations available at this time",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Show top 3 recommendations
        for i, bet in enumerate(single_bets[:3]):
            # Create custom card for recommendation
            bet_layout = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(80),
                padding=[dp(10), dp(5)],
                spacing=dp(5)
            )
            
            # Top row with team and odds
            top_row = BoxLayout(orientation="horizontal")
            team_label = Label(
                text=bet.get("team_name", "Unknown"),
                size_hint_x=0.7,
                halign="left",
                text_size=(dp(200), dp(25))
            )
            
            odds_label = Label(
                text=app.convert_odds(bet.get("odds", "0")),
                size_hint_x=0.3,
                bold=True
            )
            
            top_row.add_widget(team_label)
            top_row.add_widget(odds_label)
            
            # Bottom row with details
            bottom_row = BoxLayout(orientation="horizontal")
            
            sport_label = Label(
                text=bet.get("sport_name", ""),
                size_hint_x=0.5,
                color=[0.6, 0.6, 0.6, 1],
                font_size=dp(12),
                halign="left",
                text_size=(dp(150), dp(20))
            )
            
            win_prob = bet.get("win_probability", 0)
            prob_label = Label(
                text=f"Win prob: {win_prob:.1f}%",
                size_hint_x=0.5,
                color=[0.3, 0.7, 0.3, 1] if win_prob > 60 else [0.6, 0.6, 0.6, 1],
                font_size=dp(12),
                halign="right",
                text_size=(dp(150), dp(20))
            )
            
            bottom_row.add_widget(sport_label)
            bottom_row.add_widget(prob_label)
            
            bet_layout.add_widget(top_row)
            bet_layout.add_widget(bottom_row)
            
            # Wrap in a button for click handling
            bet_button = Button(
                background_normal="",
                background_color=[0.95, 0.95, 0.95, 1],
                size_hint_y=None,
                height=dp(80)
            )
            bet_button.add_widget(bet_layout)
            bet_button.bind(on_release=lambda x, b=bet: self.go_to_parlays())
            
            self.recommendations.add_widget(bet_button)
        
        # Add "View All" button
        view_all = Button(
            text="View All Recommendations",
            size_hint_y=None,
            height=dp(40)
        )
        view_all.bind(on_release=self.go_to_parlays)
        self.recommendations.add_widget(view_all)
    
    def load_recent_parlays(self):
        """Load recent parlays."""
        app = self.manager.parent
        db = app.db
        
        # Get recent parlays
        db.execute("""
            SELECT p.*, COUNT(pb.bet_id) as bet_count
            FROM parlays p
            LEFT JOIN parlay_bets pb ON p.id = pb.parlay_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            LIMIT 3
        """)
        
        recent_parlays = db.fetchall()
        
        if not recent_parlays:
            self.recent_parlays.add_widget(Label(
                text="No parlays found",
                size_hint_y=None,
                height=dp(40)
            ))
            return
        
        # Add parlays to the list
        for parlay in recent_parlays:
            parlay_card = ParlayCard(parlay=parlay)
            parlay_card.bind(on_release=lambda x, p=parlay: self.show_parlay_detail(p))
            self.recent_parlays.add_widget(parlay_card)
        
        # Add "View All" button
        view_all = Button(
            text="View All Parlays",
            size_hint_y=None,
            height=dp(40)
        )
        view_all.bind(on_release=self.go_to_parlays)
        self.recent_parlays.add_widget(view_all)
    
    def show_bet_detail(self, bet):
        """Navigate to bet detail screen."""
        detail_screen = self.manager.get_screen("bet_detail")
        detail_screen.load_bet(bet["id"])
        self.manager.current = "bet_detail"
    
    def show_parlay_detail(self, parlay):
        """Navigate to parlay detail screen."""
        detail_screen = self.manager.get_screen("parlay_detail")
        detail_screen.load_parlay(parlay["id"])
        self.manager.current = "parlay_detail"
    
    def go_to_bets(self, instance=None):
        """Navigate to bets screen."""
        self.manager.current = "bets"
    
    def go_to_parlays(self, instance=None):
        """Navigate to parlays screen."""
        self.manager.current = "parlays"
