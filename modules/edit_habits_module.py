"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
import pandas as pd
from models.habit import Habit


def edit_habits_ui():
    return ui.page_fluid(
        ui.layout_columns(

            ui.card(
                {"class": "edit-habits-table"},
                ui.h4("Your Habits"),
                ui.output_data_frame("habit_table")
            ),
            ui.card(
                {"class": "edit-form"},
                ui.h4("Edit / Add Habit"),
                ui.input_text("habit_name", "Habit name"),
                ui.input_select(
                    "habit_period",
                    "Period",
                    choices=["Daily", "Weekly", "Monthly", "Yearly", "Custom..."],
                    selected="Daily",
                ),
                ui.input_text(
                    "habit_custom",
                    "Custom period (e.g. for every 10 days, just type the number 10)",
                    placeholder="Only if 'Custom...' above",
                ),
                ui.input_checkbox(
                    "habit_archived", 
                    "Archived (activate to archive a habit)", 
                    value=True),
                ui.div(
                    {"class": "edit-buttons"},
                    ui.input_action_button("save_habit", "Save changes"),
                    ui.input_action_button("new_habit", "New"),
                    ui.input_action_button("delete_habit", "Delete"),
                    ui.input_action_button("home_sc", "Back"),
                )
            ),
        )
    )

def edit_habits_server(input, output, session):
    current_user = state()["current_user"]
    selected_habit_id = reactive.Value(None)

    def load_df():
        habits = Habit.list_by_user(current_user.user_id)
        rows = [h.to_dict() for h in habits]

        if not rows:
            return pd.DataFrame(columns=["habitID","HabitName","Periodtype","IsActive","LastChecked"])
        
        df = pd.DataFrame(rows)
        return df[["habitID","HabitName","Periodtype","IsActive","LastChecked"]]
    
    habits_df = reactive.Value(load_df())


    @output
    @render.data_frame
    def habit_table():
        return render.DataTable(
            habits_df(), 
            selection_mode="row", 
            editable=False
            )


    @reactive.effect
    def _on_select_row():

        sel = input.habit_table_selected_rows()
        if not sel:
            return
        
        row = habits_df().iloc[sel[0]]
        selected_habit_id.set(int(row["habitID"]))

        ui.update_text("habit_name", value=row["HabitName"])
        ui.update_checkbox("habit_active", value=bool(row["IsActive"]))

        label = str(row.get("Periodtype") or "")

        if label.lower().startswith("every "):
            ui.update_select("habit_period", selected="Custom...")
            ui.update_text("habit_custom", value=label)
        else:
            ui.update_select("habit_period", selected=label if label else "Daily")
            ui.update_text("habit_custom", value="")


    @reactive.effect
    @reactive.event(input.new_habit)
    def _new():
        selected_habit_id.set(None)
        ui.update_text("habit_name", value="")
        ui.update_select("habit_period", selected="Daily")
        ui.update_text("habit_custom", value="")
        ui.update_checkbox("habit_active", value=True)


    @reactive.effect
    @reactive.event(input.save_habit)
    def _save():
        name = (input.habit_name() or "").strip()
        if not name:
            ui.notification_show("Habit name is required.", type="error")
            return
        period_sel = input.habit_period()
        custom = (input.habit_custom() or "").strip()
        is_active = 1 if input.habit_active() else 0


        if period_sel == "Custom...":
            if not custom:
                ui.notification_show("Enter a custom period like 'every 10 days'.", type="error")
                return
            period_str = custom
        else:
            period_str = period_sel

        if selected_habit_id() is None:
            try:
                Habit.create(current_user.user_id, name, period_str, is_active)
            except Exception as e:
                ui.notification_show(f"Could not create habit: {e}", type="error")
                return
        else:
            h = Habit.get(selected_habit_id())
            if not h:
                ui.notification_show("Selected habit no longer exists.", type="warning")
                return
            try:
                h.update(habit_name=name, period_str=period_str, is_active=is_active)
            except Exception as e:
                ui.notification_show(f"Could not update habit: {e}", type="error")
                return

        habits_df(load_df())
        selected_habit_id.set(None)
        ui.notification_show("Saved.", type="message")

    @reactive.effect
    @reactive.event(input.archive_habit)
    def _archive():
        if selected_habit_id() is None:
            ui.notification_show("Select a habit to archive.", type="warning")
            return
        h = Habit.get(selected_habit_id())
        if not h:
            ui.notification_show("Selected habit no longer exists.", type="warning")
            return
        h.archive()
        habits_df(load_df())
        selected_habit_id.set(None)
        ui.notification_show("Archived.", type="message")

    @reactive.effect
    @reactive.event(input.delete_habit)
    def _delete():
        if selected_habit_id() is None:
            ui.notification_show("Select a habit to delete.", type="warning")
            return
        # tiny confirm modal
        ui.modal_show(
            ui.modal(
                f"Delete this habit permanently?",
                easy_close=False,
                footer=ui.div(
                    ui.input_action_button("confirm_delete_habit", "Yes, delete"),
                    ui.input_action_button("cancel_delete_habit", "Cancel")
                )
            )
        )


    # above here to be adjusted

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
    def delete_user():
        """
        handles the 'Yes, delete' button click inside the notification when the user clicks on 
        delete the current user

        This leads to the deletion of the user inside the database
        """
        user = state()["current_user"]
        if hasattr(user, "delete"):
            user.delete()
        ui.modal_remove()
        update_state(current_page = "user_selection", refresh_user =+ 1)

    @reactive.Effect
    @reactive.event(input.cancel_delete)
    def close_modal():
        """
        handles the 'cancel' button click inside the notification when the user clicks on 
        delete the current user
        """
        ui.modal_remove()


    @reactive.Effect
    @reactive.event(input.home_sc)
    def _():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")

