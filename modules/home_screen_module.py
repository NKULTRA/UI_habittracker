"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from models.user import User


def home_screen_ui():
    return ui.page_fluid(
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
        if not current_user().habits:
            return ui.p("No habits yet - create your first one through the 'Edit habits' button on the right.")
        else:
            return ui.output_table("habits_table")
    
    @output
    @render.table
    def habits_table():
        return [{"Habit" : x} for x in current_user.habits]
    
    @reactive.Effect
    @reactive.event(input.edit_habits)
    def _():
        current_page.set("edit_habits")

    @reactive.Effect
    @reactive.event(input.analyze_habits)
    def _():
        current_page.set("analyze_habits")

