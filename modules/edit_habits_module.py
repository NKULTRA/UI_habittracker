"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
import pandas as pd

def edit_habits_ui():
    return ui.page_fluid(
        ui.layout_columns(
            ui.div(
                {"class": "home-container"},
                # habits table on the left of the UI
            ui.card(
                {"class": "home-table"},
                ui.h4("Edit Habits"),
                ui.output_data_frame("editable_table"),
                ui.input_action_button("add_row", "Add new entry")
            ),
            
            # Buttons on the right side of the UI
            ui.card(
                {"class": "home-buttons"},
                ui.input_action_button("delete_user", "Delete the current user completely"),
                ui.input_action_button("home_sc", "Back to the home screen")
            )
            )
        )
    )


def edit_habits_server(input, output, session):

    editable_df = reactive.Value(
        pd.DataFrame(columns=["HabitName", "PeriodType", "IsActive"])
    )

    @output
    @render.data_frame
    def editable_table():
        return render.DataTable(editable_df(), editable=True)


    @reactive.Effect
    @reactive.event(input.add_row)
    def add_row():
        df = editable_df().copy()
        new_row = {"HabitName": "", "PeriodType": "", "IsActive": True}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        editable_df.set(df)


    @reactive.Effect
    @reactive.event(input.apply_changes)
    def save_habits():
        """
        handles the button to go back to the user selection
        """
        df = habit_data()
        user = state()["current_user"]

        for _, row in df.iterrows():
            if row["HabitName"]:
                Habit.create(
                    user_id=user.user_id,
                    name=row["HabitName"],
                    period=row["Period"],
                    is_active=row["IsActive"]
                )
        
        # Redirect to home or clear table
        habit_data(pd.DataFrame(columns=["HabitName", "Period", "IsActive"]))
        update_state(current_page="home_screen")

    @reactive.Effect
    @reactive.event(input.delete_user)
    def show_delete_modal():
        """
        handles the button click on user deletion
        """
        ui.modal_show(
            ui.modal(
                "Do you really want to delete the current user? This cannot be reversed.",
                easy_close=False,
                footer=(
                    ui.input_action_button("confirm_delete", "Yes, delete"),
                    ui.input_action_button("cancel_delete", "Cancel")
                    )
            )
        )

    @reactive.Effect
    @reactive.event(input.confirm_delete)
    def _():
        user = state()["current_user"]
        if hasattr(user, "delete"):
            user.delete()
        ui.modal_remove()
        update_state(current_page = "user_selection", refresh_user =+ 1)

    @reactive.Effect
    @reactive.event(input.cancel_delete)
    def _():
        ui.modal_remove()


    @reactive.Effect
    @reactive.event(input.home_sc)
    def _():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")

