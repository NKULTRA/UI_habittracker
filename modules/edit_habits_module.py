"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
import pandas as pd
from models.habit import Habit
import re


def edit_habits_ui():
    return ui.page_fluid(
        ui.layout_columns(

            ui.card(
                {"class": "edit-habits-table"},
                ui.h4("Your Habits"),
                # table on the left of the UI
                ui.output_data_frame("habit_table")
            ),
            ui.card(
                # form on the right side
                {"class": "edit-form"},
                ui.h4("Edit / Add Habit"),
                ui.input_text("habit_name", "Habit Name"),
                ui.input_select(
                    "habit_period",
                    "Period",
                    choices=["Daily", "Weekly", "Monthly", "Yearly", "Custom"],
                    selected="Daily"
                ),                
                ui.panel_conditional(
                    "input.habit_period === 'Custom'",
                    ui.input_text(
                        "habit_custom",
                        "Custom period (e.g. enter 10 for 'every 10 days')",
                        placeholder="Custom range…"
                    )
                ),
                ui.input_select(
                    "habit_status",
                    "Status",
                    choices=["Archived", "Active"],
                    selected="Active"
                ),
                ui.div(
                    # different buttons on the right side
                    {"class": "d-flex flex-wrap gap-2"},
                    ui.input_action_button("save_habit", "Save changes"),
                    ui.input_action_button("delete_habit", "Delete"),
                    ui.input_action_button("delete_user", "Delete User"),
                    ui.input_action_button("home_sc", "Back")
                ),
                # infotext
                ui.div(
                    {"class": "alert alert-custom d-flex align-items-center mb-2", "role": "alert"},
                    ui.HTML(
                        "To add a new habit, give it a name, choose a period, and click 'Save Changes'.<br>"
                        "To edit a habit, click the associated row in the table on the left. After changes click 'Save Changes'.<br>"
                        "To archive a habit, set its status to 'Archived' (reactivate the same way).<br>"
                        "To delete a habit, select it, then click 'Delete'.<br>"
                        "'Delete User' will permanently remove the current user — use with caution!"
                    )
                )
            ),
        )
    )


def edit_habits_server(input, output, session):


    selected_habit_id = reactive.Value(None)
    _refresh_table = reactive.Value(0) # this variable is to trigger re-render / recalculate table e.g. after deletion


    def habits_raw_df():
        """
        creates the 'raw' dataframe, this is because for display reasons the column names 
        needs to be renamed, for queries etc. the original dataframe remains useful
        """
        user = state()["current_user"]
        _ = _refresh_table() # creates dependency, this variable is to trigger re-render / recalculate

        cols = ["habitID","HabitName","Periodtype","IsActive", "DateCreated", "LastChecked"]

        if user is None:
            return pd.DataFrame(columns=cols)

        # get all habits from current user, including archived
        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]
        
        if not rows:
            return pd.DataFrame(columns=cols)

        return pd.DataFrame(rows)[cols]


    @reactive.Calc
    def habits_df():
        """
        creates the dataframe for the display, with renamed columns
        builds on the raw dataframe
        """
        raw = habits_raw_df().copy()

        if raw.empty:
            return pd.DataFrame(columns=["Habit Name","Period","Status", "Created at","Last Checked"])

        raw["IsActive"] = raw["IsActive"].map({1: "Active", 0: "Archived"})

        raw.rename(columns={
            "HabitName": "Habit Name",
            "Periodtype": "Period",
            "IsActive": "Status",
            "DateCreated": "Created at",
            "LastChecked": "Last Checked",
        }, inplace=True)

        return raw[["Habit Name","Period","Status","Created at","Last Checked"]]


    @output
    @render.data_frame
    def habit_table():
        """
        renders the habits_df as a Datatable, with this form it is possible to select rows
        """
        return render.DataTable(
            habits_df(), 
            selection_mode="row", 
            editable=False
            )


    def reset_form():
        """
        this is just a safety method to reset the form
        because sometimes after habit deletion it throws an error when the 'old' data is still there
        """
        selected_habit_id.set(None)
        ui.update_text("habit_name", value="")
        ui.update_select("habit_period", selected="Daily")
        ui.update_select("habit_status", selected="Active")
        ui.update_text("habit_custom", value="")


    @reactive.effect
    def _on_select_row():
        """
        handles the user click on one of the habits
        """
        sel = input.habit_table_selected_rows()
        df_disp = habits_df()
        df_raw  = habits_raw_df()

        if not sel or df_disp.empty:
            reset_form()
            return

        idx = sel[0]

        # reset the index, this is because after habit deletion it throws sometimes an index error
        if idx is None or idx < 0 or idx >= len(df_disp) or idx >= len(df_raw):
            reset_form()
            return

        hid = int(df_raw.iloc[idx]["habitID"])
        selected_habit_id.set(hid)

        # load the data from the clicked row from the table into the form
        row = df_disp.iloc[idx]
        ui.update_text("habit_name", value=row["Habit Name"])
        ui.update_select("habit_status", selected=row["Status"])

        label = row.get("Period")

        # handles custom - period habits
        if label not in ("Daily", "Weekly", "Monthly", "Yearly"):
            match = re.search(r"\b\d+\b", label)
            ui.update_select("habit_period", selected="Custom")
            ui.update_text("habit_custom", value=match.group())
        else:
            ui.update_select("habit_period", selected=label)


    @reactive.effect
    @reactive.event(input.save_habit)
    def _save():
        """
        handles what happens when the user clicks on the 'Save Changes' button
        it creates either a new habit in the database or updates an existing one
        """
        user = state()["current_user"]
        name = input.habit_name().strip()

        if not name:
            ui.notification_show("Habit name is required.", type="error")
            return
        
        period_sel = input.habit_period()
        is_active = 1 if input.habit_status() == "Active" else 0

        if period_sel == "Custom":
            custom = input.habit_custom()
            if not custom:
                ui.notification_show("Enter a custom period in the text field in days (e.g. 10)", type="error")
                return
            period_str = custom
        else:
            period_str = period_sel

        # to catch any errors with the selected habit or when try to write in the database
        if selected_habit_id() is None:
            try:
                Habit.create(user.user_id, name, period_str, is_active)
            except Exception as e:
                # here maybe better understandable messages
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
            
        _refresh_table.set(_refresh_table() + 1)
        selected_habit_id.set(None)
        ui.notification_show("Saved.", type="message")


    @reactive.effect
    @reactive.event(input.delete_habit)
    def _delete():
        """
        handles the button click on 'Delete'
        will delete a habit and all its activities from the database
        """
        if selected_habit_id() is None:
            ui.notification_show("Select a habit to delete.", type="warning")
            return
        
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


    @reactive.Effect
    @reactive.event(input.confirm_delete_habit)
    def delete_habit():
        """
        handles the 'Yes, delete' button click inside the notification when the user clicks on 
        delete the habit

        This leads to the deletion of the habit inside the database
        """
        if selected_habit_id() is None:
            ui.modal_remove()
            return

        h = Habit.get(selected_habit_id())
        if h:
            try:
                h.delete() 
                ui.notification_show("Habit deleted.", type="message")
            except Exception as e:
                ui.notification_show(f"Delete failed: {e}", type="error")
                return

        _refresh_table.set(_refresh_table() + 1)
        reset_form()
        selected_habit_id.set(None)
        ui.modal_remove()


    @reactive.Effect
    @reactive.event(input.cancel_delete_habit)
    def close_habit_delete_modal():
        """
        handles the 'cancel' button click inside the notification when the user clicks on 
        delete the current user
        """
        ui.modal_remove()


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
        update_state(current_page="user_selection",
             refresh_user=state()["refresh_user"] + 1)


    @reactive.Effect
    @reactive.event(input.cancel_delete)
    def close_user_delete_modal():
        """
        handles the 'cancel' button click inside the notification when the user clicks on 
        delete the current user
        """
        ui.modal_remove()


    @reactive.Effect
    @reactive.event(input.home_sc)
    def edit_go_home():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")

