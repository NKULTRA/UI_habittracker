"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
import pandas as pd
from models.habit import Habit


def home_screen_ui():
    return ui.page_fluid(
        ui.layout_columns(
            ui.div(
                {"class": "home-container"},
                # habits table on the left of the UI
            ui.card(
                {"class": "home-table"},
                ui.h4("Your Habits"),
                ui.output_ui("habits_display"),
                ui.output_data_frame("habits_tbl_home")
            ),
            
            # Buttons on the right side of the UI
            ui.card(
                {"class": "home-buttons"},
                ui.input_action_button("edit_habits", "Edit Habits"),
                ui.input_action_button("analyze_habits", "Analyze Habits"),
                ui.input_action_button("user_selection", "Back to user selection")
            )
            )
        )
    )


def home_screen_server(input, output, session):

    @reactive.Calc
    def habits_df():
        user = state()["current_user"]
        cols = ["habitID","HabitName","Periodtype","IsActive","LastChecked"]

        if user is None:
            return pd.DataFrame(columns=cols)

        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]

        if not rows:
            return pd.DataFrame(columns=cols)

        return pd.DataFrame(rows)[cols]
    
    @output
    @render.ui
    def habits_display():
        if habits_df().empty:
            return ui.p("No habits yet - create your first one through the 'Edit habits' button on the right.")
        return None 
    
    @output
    @render.data_frame
    def habits_tbl_home():
        if habits_df().empty:
            return None
        return render.DataTable(
            habits_df(), 
            selection_mode="none",
            editable=False
        )


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
    @reactive.event(input.edit_habits, ignore_init=True)
    def _():
        """
        handles the button click on edit habits
        """
        update_state(current_page="edit_habits")

    @reactive.Effect
    @reactive.event(input.analyze_habits, ignore_init=True)
    def _():
        """
        handles the button click on analyze habits
        """
        update_state(current_page="analyze_habits")

