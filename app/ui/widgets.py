#!/usr/bin/env python3
"""
Widgets Module for BettingBuddy app.

Contains custom widgets used across the app.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.properties import StringProperty, ListProperty, BooleanProperty, ObjectProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior

from datetime import datetime


class SummaryCard(BoxLayout):
    """Summary card widget for dashboard statistics."""
    
    title = StringProperty("")
    value = StringProperty("")
    icon = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(5)
        
        # Use background
        self.background = Image(
            source="",  # No image source needed
            allow_stretch=True,
            keep_ratio=False,
            color=[0.95, 0.95, 0.95, 1]  # Light gray background
        )
        
        # Label for title
        self.title_label = Label(
            text=self.title,
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=[0.4, 0.4, 0.4, 1]
        )
        
        # Label for value
        self.value_label = Label(
            text=self.value,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(24),
            bold=True
        )
        
        # Add widgets
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)
        
        # Bind properties for updates
        self.bind(title=self.update_title)
        self.bind(value=self.update_value)
    
    def update_title(self, instance, value):
        """Update title text."""
        self.title_label.text = value
    
    def update_value(self, instance, value):
        """Update value text."""
        self.value_label.text = value


class BetCard(ButtonBehavior, BoxLayout):
    """Card widget for displaying a bet."""
    
    bet = ObjectProperty(None)
    in_parlay = BooleanProperty(False)
    selectable = BooleanProperty(False)
    remove_callback = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(5)
        
        if not self.bet:
            # Empty card
            self.add_widget(Label(text="No bet data"))
            return
        
        # Main content layout
        self.content = BoxLayout(orientation="vertical")
        
        # Top row with team and odds
        self.top_row = BoxLayout(orientation="horizontal")
        
        self.team_label = Label(
            text=self.bet.get("team_name", "Unknown"),
            size_hint_x=0.7,
            text_size=(dp(200), dp(25)),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        
        # Get app instance for odds conversion
        app = None
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'parent'):
            app = self.parent.parent
        
        odds_text = self.bet.get("odds", "+000")
        if app and hasattr(app, 'convert_odds'):
            odds_text = app.convert_odds(odds_text)
        
        self.odds_label = Label(
            text=odds_text,
            size_hint_x=0.3,
            bold=True
        )
        
        self.top_row.add_widget(self.team_label)
        self.top_row.add_widget(self.odds_label)
        
        # Middle row with description
        self.description_label = Label(
            text=self.bet.get("description", ""),
            size_hint_y=None,
            height=dp(20),
            font_size=dp(12),
            color=[0.5, 0.5, 0.5, 1],
            text_size=(dp(280), dp(20)),
            halign="left",
            valign="middle",
            shorten=True
        )
        
        # Bottom row with details and status
        self.bottom_row = BoxLayout(orientation="horizontal")
        
        # Format date if available
        date_text = ""
        event_date = self.bet.get("event_date")
        if event_date:
            try:
                # Try to parse date
                date_obj = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                date_text = date_obj.strftime("%b %d, %I:%M %p")
            except (ValueError, AttributeError):
                date_text = event_date
        
        sport_text = self.bet.get("sport_name", "")
        details_text = f"{sport_text} • {date_text}" if date_text else sport_text
        
        self.details_label = Label(
            text=details_text,
            size_hint_x=0.7,
            font_size=dp(12),
            color=[0.5, 0.5, 0.5, 1],
            text_size=(dp(200), dp(20)),
            halign="left",
            valign="middle",
            shorten=True
        )
        
        status = self.bet.get("status", "pending")
        status_color = [0.3, 0.3, 0.3, 1]  # Gray for pending
        if status == "won":
            status_color = [0.2, 0.7, 0.2, 1]  # Green for won
        elif status == "lost":
            status_color = [0.7, 0.2, 0.2, 1]  # Red for lost
        
        self.status_label = Label(
            text=status.capitalize(),
            size_hint_x=0.3,
            font_size=dp(12),
            color=status_color
        )
        
        self.bottom_row.add_widget(self.details_label)
        self.bottom_row.add_widget(self.status_label)
        
        # Add all rows to content
        self.content.add_widget(self.top_row)
        self.content.add_widget(self.description_label)
        self.content.add_widget(self.bottom_row)
        
        # Add remove button if in parlay
        if self.in_parlay:
            self.layout = BoxLayout(orientation="horizontal")
            
            self.layout.add_widget(self.content)
            
            self.remove_btn = Button(
                text="X",
                size_hint_x=None,
                width=dp(30),
                background_color=[0.8, 0.2, 0.2, 1]
            )
            self.remove_btn.bind(on_release=self.remove_from_parlay)
            
            self.layout.add_widget(self.remove_btn)
            self.add_widget(self.layout)
        else:
            self.add_widget(self.content)
    
    def remove_from_parlay(self, instance):
        """Call the remove callback."""
        if self.remove_callback:
            self.remove_callback()


class ParlayCard(ButtonBehavior, BoxLayout):
    """Card widget for displaying a parlay."""
    
    parlay = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(5)
        
        if not self.parlay:
            # Empty card
            self.add_widget(Label(text="No parlay data"))
            return
        
        # Top row with bet count and stake
        self.top_row = BoxLayout(orientation="horizontal")
        
        bet_count = self.parlay.get("bet_count", 0)
        bet_text = f"{bet_count} Bet Parlay" if bet_count == 1 else f"{bet_count} Bet Parlay"
        
        self.count_label = Label(
            text=bet_text,
            size_hint_x=0.7,
            bold=True,
            text_size=(dp(200), dp(25)),
            halign="left",
            valign="middle"
        )
        
        stake = self.parlay.get("stake", 0)
        self.stake_label = Label(
            text=f"${stake:.2f}",
            size_hint_x=0.3
        )
        
        self.top_row.add_widget(self.count_label)
        self.top_row.add_widget(self.stake_label)
        
        # Middle row with odds and payout
        self.middle_row = BoxLayout(orientation="horizontal")
        
        # Get app instance for odds conversion
        app = None
        if hasattr(self, 'parent') and self.parent and hasattr(self.parent, 'parent'):
            app = self.parent.parent
        
        odds_text = self.parlay.get("total_odds", "+000")
        if app and hasattr(app, 'convert_odds'):
            odds_text = app.convert_odds(odds_text)
        
        self.odds_label = Label(
            text=f"Odds: {odds_text}",
            size_hint_x=0.6,
            text_size=(dp(180), dp(20)),
            halign="left",
            valign="middle"
        )
        
        payout = self.parlay.get("potential_payout", 0)
        self.payout_label = Label(
            text=f"Payout: ${payout:.2f}",
            size_hint_x=0.4,
            bold=True,
            color=[0.2, 0.7, 0.2, 1],
            text_size=(dp(120), dp(20)),
            halign="right",
            valign="middle"
        )
        
        self.middle_row.add_widget(self.odds_label)
        self.middle_row.add_widget(self.payout_label)
        
        # Bottom row with date and status
        self.bottom_row = BoxLayout(orientation="horizontal")
        
        # Format creation date
        date_text = ""
        created_at = self.parlay.get("created_at")
        if created_at:
            try:
                # Try to parse date
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_text = date_obj.strftime("%b %d, %Y")
            except (ValueError, AttributeError):
                date_text = created_at
        
        self.date_label = Label(
            text=date_text,
            size_hint_x=0.7,
            font_size=dp(12),
            color=[0.5, 0.5, 0.5, 1],
            text_size=(dp(200), dp(20)),
            halign="left",
            valign="middle"
        )
        
        status = self.parlay.get("status", "pending")
        status_color = [0.3, 0.3, 0.3, 1]  # Gray for pending
        if status == "won":
            status_color = [0.2, 0.7, 0.2, 1]  # Green for won
        elif status == "lost":
            status_color = [0.7, 0.2, 0.2, 1]  # Red for lost
        
        self.status_label = Label(
            text=status.capitalize(),
            size_hint_x=0.3,
            font_size=dp(12),
            color=status_color
        )
        
        self.bottom_row.add_widget(self.date_label)
        self.bottom_row.add_widget(self.status_label)
        
        # Add all rows
        self.add_widget(self.top_row)
        self.add_widget(self.middle_row)
        self.add_widget(self.bottom_row)


class RecommendationCard(ButtonBehavior, BoxLayout):
    """Card widget for displaying a recommendation."""
    
    recommendation = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = [dp(10), dp(5)]
        self.spacing = dp(5)
        
        if not self.recommendation:
            # Empty card
            self.add_widget(Label(text="No recommendation data"))
            return
        
        # Header - recommendation type and value
        self.header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30)
        )
        
        rec_type = self.recommendation.get("recommendation_type", "")
        if rec_type == "single_bets":
            type_text = "Single Bet"
        else:
            leg_count = len(self.recommendation.get("bets", []))
            type_text = f"{leg_count}-Leg Parlay"
        
        self.type_label = Label(
            text=type_text,
            size_hint_x=0.7,
            bold=True,
            text_size=(dp(200), dp(30)),
            halign="left",
            valign="middle"
        )
        
        win_prob = self.recommendation.get("win_probability", 0)
        self.value_label = Label(
            text=f"Win prob: {win_prob:.1f}%",
            size_hint_x=0.3,
            color=[0.2, 0.7, 0.2, 1] if win_prob > 60 else [0.5, 0.5, 0.5, 1],
            text_size=(dp(100), dp(30)),
            halign="right",
            valign="middle"
        )
        
        self.header.add_widget(self.type_label)
        self.header.add_widget(self.value_label)
        
        # Teams list
        self.teams_list = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(50)
        )
        
        bets = self.recommendation.get("bets", [])
        for i, bet in enumerate(bets[:3]):  # Show up to 3 bets
            team_name = bet.get("team_name", "Unknown")
            odds = bet.get("odds", "+000")
            
            team_row = BoxLayout(orientation="horizontal")
            
            team_label = Label(
                text=team_name,
                size_hint_x=0.7,
                font_size=dp(12),
                text_size=(dp(200), dp(15)),
                halign="left",
                valign="middle",
                shorten=True
            )
            
            odds_label = Label(
                text=odds,
                size_hint_x=0.3,
                font_size=dp(12),
                text_size=(dp(100), dp(15)),
                halign="right",
                valign="middle"
            )
            
            team_row.add_widget(team_label)
            team_row.add_widget(odds_label)
            
            self.teams_list.add_widget(team_row)
            
        if len(bets) > 3:
            # Indicate there are more bets
            more_label = Label(
                text=f"+ {len(bets) - 3} more...",
                size_hint_y=None,
                height=dp(15),
                font_size=dp(12),
                color=[0.5, 0.5, 0.5, 1]
            )
            self.teams_list.add_widget(more_label)
        
        # Footer with odds and potential payout
        self.footer = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30)
        )
        
        decimal_odds = self.recommendation.get("decimal_odds", 1.0)
        american_odds = self.recommendation.get("american_odds", "+100")
        
        self.odds_label = Label(
            text=f"Total odds: {american_odds}",
            size_hint_x=0.7,
            font_size=dp(12),
            text_size=(dp(200), dp(30)),
            halign="left",
            valign="middle"
        )
        
        expected_value = self.recommendation.get("expected_value", 0)
        ev_color = [0.2, 0.7, 0.2, 1] if expected_value > 0 else [0.7, 0.2, 0.2, 1]
        self.ev_label = Label(
            text=f"EV: {expected_value:.2f}",
            size_hint_x=0.3,
            font_size=dp(12),
            color=ev_color,
            text_size=(dp(100), dp(30)),
            halign="right",
            valign="middle"
        )
        
        self.footer.add_widget(self.odds_label)
        self.footer.add_widget(self.ev_label)
        
        # Add all sections
        self.add_widget(self.header)
        self.add_widget(self.teams_list)
        self.add_widget(self.footer)


class FilterButton(Button):
    """Button for filter selection with active state."""
    
    active = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.update_state()
        
        # Bind to the active property
        self.bind(active=self.update_state)
    
    def update_state(self, *args):
        """Update the button appearance based on active state."""
        if self.active:
            self.background_color = [0.2, 0.5, 0.9, 1]  # Highlighted color
        else:
            self.background_color = [0.4, 0.4, 0.4, 1]  # Regular color
