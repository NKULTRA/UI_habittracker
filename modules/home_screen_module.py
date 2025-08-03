"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from models.user import User


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


def home_screen_server(input, output, session, current_page, current_user):
    @output
    @render.ui
    def habits_display():
        """
        creates the habits table on the left of the UI
        """
        user = current_user()

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
        return [{"Habit" : x} for x in current_user.habits]
    
    @reactive.Effect
    @reactive.event(input.user_selection)
    def _():
        """
        handles the button to go back to the user selection
        """
        current_user.set(None)
        current_page.set("user_selection")

    @reactive.Effect
    @reactive.event(input.edit_habits)
    def _():
        """
        handles the button click on edit habits
        """
        current_page.set("edit_habits")

    @reactive.Effect
    @reactive.event(input.analyze_habits)
    def _():
        """
        handles the button click on analyze habits
        """
        current_page.set("analyze_habits")

