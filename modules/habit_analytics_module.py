"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import ui, render


def habit_analytics_ui():
    return ui.page_fluid(
        ui.h2("My modular shiny app"),
        ui.output_text("greeting")
    )


def habit_analytics_server(input, output, session):
    pass