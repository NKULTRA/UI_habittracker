"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui


def home_screen_ui():
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


def home_screen_server(input, output, session, current_page, current_user):
    @output
    @render.text
    def greeting():
        return "welcome :)"
    
    def greeting_again():
        return "welcome :)"
