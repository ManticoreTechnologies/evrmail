"""
Test script for the EvrMail custom browser implementation
"""

import flet as ft
from evrmail.gui.browser import FletBrowser

def main(page: ft.Page):
    # Configure the window
    page.title = "EvrMail Browser Test"
    page.window_width = 1200
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # Create our browser component
    browser = FletBrowser()
    
    # Add it to the page
    page.add(browser)
    
    # Make it reload once everything is set up
    def delayed_init():
        # Give the browser time to initialize
        if browser.tabs and len(browser.tabs) > 0:
            # Navigate to a test URL
            browser.tabs[0].navigate("https://flet.dev")
    
    # Schedule delayed init
    page.on_load = lambda _: delayed_init()

if __name__ == "__main__":
    ft.app(target=main) 