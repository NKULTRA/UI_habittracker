"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state


def home_screen_ui():
    return ui.page_fluid(
        ui.layout_columns(  
            ui.card(
                ui.input_action_button("user_selection", "Back to user selection"),
                width=12)
            ),
        ui.layout_columns(
            # habits table on the left of the UI
            ui.card(
                ui.h4("Your Habits"),
                ui.output_ui("habits_display"),
                width=8
            ),
            
            # Buttons on the right side of the UI
            ui.card(
                ui.input_action_button("edit_habits", "Edit Habits"),
                ui.input_action_button("analyze_habits", "Analyze Habits"),
                width=4
            )
        )
    )


def home_screen_server(input, output, session):
    @output
    @render.ui
    def habits_display():
        """
        creates the habits table on the left of the UI
        """
        user = state()["current_user"]

        if user is None:
            return ui.div()
        elif not user.habits:
            return ui.p("No habits yet - create your first one through the 'Edit habits' button on the right.")
        else:
            return ui.output_table("habits_table")
    
    @output
    @render.table
    def habits_table():
        """
        loads the habits when there are any
        """
        return [{"Habit" : x} for x in state()["current_user"].habits]
    
    @reactive.Effect
    @reactive.event(input.user_selection)
    def _():
        """
        handles the button to go back to the user selection
        """
        update_state(
            current_user=None,
            current_page="user_selection"
        )

    @reactive.Effect
    @reactive.event(input.edit_habits)
    def _():
        """
        handles the button click on edit habits
        """
        update_state(current_page="edit_habits")

    @reactive.Effect
    @reactive.event(input.analyze_habits)
    def _():
        """
        handles the button click on analyze habits
        """
        update_state(current_page="analyze_habits")

