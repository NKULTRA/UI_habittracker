"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state


def habit_analytics_ui():
    return ui.page_fluid(
        ui.layout_columns(
            ui.div(
                {"class": "home-container"},

            ui.card(
                {"class": "home-table"},
                ui.h4("Analyze habits"),
            ),
            
            ui.card(
                {"class": "home-buttons"},
                ui.input_action_button("home_sc", "Back to the home screen")
            )
            )
        )
    )


def habit_analytics_server(input, output, session):

    @reactive.Effect
    @reactive.event(input.home_sc)
    def _():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")
