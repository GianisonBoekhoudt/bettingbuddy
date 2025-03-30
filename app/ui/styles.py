#!/usr/bin/env python3
"""
Styles Module for BettingBuddy app.

Contains style constants and helper functions for UI styling.
"""

from kivy.metrics import dp
from kivy.utils import get_color_from_hex


# Color constants
PRIMARY_COLOR = get_color_from_hex('#2196F3')  # Material Blue
DARK_PRIMARY_COLOR = get_color_from_hex('#1976D2')  # Darker Blue
ACCENT_COLOR = get_color_from_hex('#FF9800')  # Orange
BACKGROUND_COLOR = get_color_from_hex('#F5F5F5')  # Light Gray
TEXT_PRIMARY_COLOR = get_color_from_hex('#212121')  # Almost Black
TEXT_SECONDARY_COLOR = get_color_from_hex('#757575')  # Medium Gray
DIVIDER_COLOR = get_color_from_hex('#BDBDBD')  # Light Gray
SUCCESS_COLOR = get_color_from_hex('#4CAF50')  # Green
ERROR_COLOR = get_color_from_hex('#F44336')  # Red
WARNING_COLOR = get_color_from_hex('#FFC107')  # Amber

# Sizes
HEADER_HEIGHT = dp(56)
SUBHEADER_HEIGHT = dp(48)
BUTTON_HEIGHT = dp(40)
CARD_HEIGHT = dp(100)
CARD_PADDING = dp(10)
STANDARD_SPACING = dp(8)

# Typography
H1_FONT_SIZE = dp(24)
H2_FONT_SIZE = dp(20)
H3_FONT_SIZE = dp(18)
BODY_FONT_SIZE = dp(14)
CAPTION_FONT_SIZE = dp(12)


def get_status_color(status):
    """Get color for bet status."""
    if status == 'won':
        return SUCCESS_COLOR
    elif status == 'lost':
        return ERROR_COLOR
    else:
        return TEXT_SECONDARY_COLOR  # Pending or other


def get_win_probability_color(probability):
    """Get color based on win probability."""
    if probability >= 75:
        return SUCCESS_COLOR
    elif probability >= 50:
        return get_color_from_hex('#8BC34A')  # Light Green
    elif probability >= 33:
        return WARNING_COLOR
    else:
        return ERROR_COLOR


def get_expected_value_color(ev):
    """Get color based on expected value."""
    if ev > 0.2:
        return SUCCESS_COLOR
    elif ev > 0:
        return get_color_from_hex('#8BC34A')  # Light Green
    elif ev > -0.1:
        return WARNING_COLOR
    else:
        return ERROR_COLOR


def create_gradient(start_color, end_color, steps=100):
    """Create a gradient between two colors."""
    r1, g1, b1, a1 = start_color
    r2, g2, b2, a2 = end_color
    
    r_step = (r2 - r1) / steps
    g_step = (g2 - g1) / steps
    b_step = (b2 - b1) / steps
    a_step = (a2 - a1) / steps
    
    gradient = []
    
    for i in range(steps + 1):
        r = r1 + (r_step * i)
        g = g1 + (g_step * i)
        b = b1 + (b_step * i)
        a = a1 + (a_step * i)
        gradient.append([r, g, b, a])
    
    return gradient
