"""
BettingBuddy Animations Module

This module contains animation utilities for enhancing the app's UI.
"""

from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.metrics import dp

def slide_in_right(widget, duration=0.3, delay=0):
    """
    Slide a widget in from the right.
    
    Args:
        widget (Widget): The widget to animate
        duration (float): Animation duration in seconds
        delay (float): Delay before starting animation
    """
    # Store original position
    original_x = widget.x
    
    # Move widget off-screen
    widget.x = Window.width
    
    # Animate back to original position
    anim = Animation(x=original_x, duration=duration, t='out_quad')
    anim.start(widget)

def slide_in_left(widget, duration=0.3, delay=0):
    """
    Slide a widget in from the left.
    
    Args:
        widget (Widget): The widget to animate
        duration (float): Animation duration in seconds
        delay (float): Delay before starting animation
    """
    # Store original position
    original_x = widget.x
    
    # Move widget off-screen
    widget.x = -widget.width
    
    # Animate back to original position
    anim = Animation(x=original_x, duration=duration, t='out_quad')
    if delay > 0:
        anim = Animation(duration=delay) + anim
    anim.start(widget)

def fade_in(widget, duration=0.3, delay=0):
    """
    Fade in a widget.
    
    Args:
        widget (Widget): The widget to animate
        duration (float): Animation duration in seconds
        delay (float): Delay before starting animation
    """
    widget.opacity = 0
    anim = Animation(opacity=1, duration=duration)
    if delay > 0:
        anim = Animation(duration=delay) + anim
    anim.start(widget)

def fade_out(widget, duration=0.3, delay=0):
    """
    Fade out a widget.
    
    Args:
        widget (Widget): The widget to animate
        duration (float): Animation duration in seconds
        delay (float): Delay before starting animation
    """
    anim = Animation(opacity=0, duration=duration)
    if delay > 0:
        anim = Animation(duration=delay) + anim
    anim.start(widget)

def pulse(widget, scale=1.1, duration=0.2):
    """
    Create a pulse animation for a widget.
    
    Args:
        widget (Widget): The widget to animate
        scale (float): Maximum scale factor
        duration (float): Animation duration in seconds
    """
    anim = Animation(scale=scale, duration=duration, t='out_quad') + \
           Animation(scale=1.0, duration=duration, t='in_out_quad')
    anim.start(widget)

def shake(widget, intensity=5, duration=0.5):
    """
    Create a shake animation for a widget.
    
    Args:
        widget (Widget): The widget to animate
        intensity (float): Shake intensity in dp
        duration (float): Animation duration in seconds
    """
    orig_x = widget.x
    
    # Create sequence of small movements
    anim = Animation(x=orig_x + dp(intensity), duration=duration/5, t='in_out_quad')
    anim += Animation(x=orig_x - dp(intensity), duration=duration/5, t='in_out_quad')
    anim += Animation(x=orig_x + dp(intensity/2), duration=duration/5, t='in_out_quad')
    anim += Animation(x=orig_x - dp(intensity/2), duration=duration/5, t='in_out_quad')
    anim += Animation(x=orig_x, duration=duration/5, t='in_out_quad')
    
    anim.start(widget)

def bounce_in(widget, duration=0.5):
    """
    Create a bounce-in animation for a widget.
    
    Args:
        widget (Widget): The widget to animate
        duration (float): Animation duration in seconds
    """
    # Store original position and set initial position
    widget.scale = 0.5
    widget.opacity = 0
    
    # Create animation
    anim = Animation(scale=1.1, opacity=1, duration=duration*0.6, t='out_quad')
    anim += Animation(scale=1.0, duration=duration*0.4, t='in_out_bounce')
    
    anim.start(widget)

def slide_transition(screen_manager, direction='left'):
    """
    Configure the screen manager to use slide transitions.
    
    Args:
        screen_manager (ScreenManager): The screen manager to configure
        direction (str): The slide direction ('left', 'right', 'up', 'down')
    """
    from kivy.uix.screenmanager import SlideTransition
    screen_manager.transition = SlideTransition(direction=direction)

def fade_transition(screen_manager, duration=0.3):
    """
    Configure the screen manager to use fade transitions.
    
    Args:
        screen_manager (ScreenManager): The screen manager to configure
        duration (float): The transition duration
    """
    from kivy.uix.screenmanager import FadeTransition
    screen_manager.transition = FadeTransition(duration=duration)

def card_flip(front_widget, back_widget, duration=0.5):
    """
    Create a 3D card flip animation between two widgets.
    
    Args:
        front_widget (Widget): The front-facing widget
        back_widget (Widget): The back-facing widget
        duration (float): Animation duration in seconds
    """
    # Set initial states
    back_widget.opacity = 0
    
    # Animate front widget (scaling down horizontally)
    anim1 = Animation(scale_x=0.1, duration=duration/2, t='in_out_quad')
    
    # Chain with back widget animation
    anim2 = Animation(scale_x=1.0, duration=duration/2, t='in_out_quad')
    
    # Function to switch widgets
    def switch_widgets(animation, widget):
        front_widget.opacity = 0
        back_widget.opacity = 1
        back_widget.scale_x = 0.1
        anim2.start(back_widget)
    
    anim1.bind(on_complete=switch_widgets)
    anim1.start(front_widget)

# Make sure to import Window
from kivy.core.window import Window