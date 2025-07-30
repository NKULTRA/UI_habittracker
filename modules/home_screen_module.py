"""
Module creates the page after the login
The home screen
"""
from shiny import ui, render


home_screen_ui = ui.page_fluid(
    ui.h2("My modular shiny app"),
    ui.output_text("greeting")
)

def home_screen_server(input, output, session):
    @output
    @render.text
    def greeting():
        return "Hello from server"