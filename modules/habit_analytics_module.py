"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import render, ui


def habit_analytics_ui():
    return ui.page_fluid(
        ui.h2("My modular shiny app"),
        ui.input_text("username", "Enter your username:"),
        ui.output_text("greeting"),
        ui.card(
            ui.card_header(
                title = "Hello"
            ),
            ui.card_body(
                ui.output_text("greeting_again")
            )
        )
    )


def habit_analytics_server(input, output, session):
    @output
    @render.text
    def greeting():
        return "welcome :)"
    
    def greeting_again():
        return "welcome :)"
