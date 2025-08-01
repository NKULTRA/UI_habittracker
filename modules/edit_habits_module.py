"""
Module creates the Edit Habits Screen 
after the user clicks the button on the home screen
"""
from shiny import ui, render


def edit_habits_ui():
    return ui.page_fluid(
        ui.h2("My modular shiny app"),
        ui.output_text("greeting")
    )


def edit_habits_server(input, output, session):
    pass