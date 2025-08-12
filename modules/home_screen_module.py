"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
from services.database import mark_habit_as_checked
from models.habit import Habit
from datetime import datetime, date, timedelta


def home_screen_ui():
    return ui.page_fluid(
        ui.layout_columns(
            ui.div(
                {"class": "home-container"},
                # habits table on the left of the UI
                ui.card(
                    {"class": "home-table"},
                    ui.h4("Your Habits"),
                    ui.output_ui("home_checks"),
                    ui.output_ui("habits_display")
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

    refresh_habits = reactive.Value(0)

    @reactive.Calc
    def _habits_for_home():
        """
        creates the basis for the visible habits on the homescreen
        seperates into habits which are due today or optional habits, which can be checked but
        it isnt necessary to do so today (weekly and the due date is not yet reached)
        """
        user = state()["current_user"]
        _ = refresh_habits()

        if user is None:
            return [], []

        # get all active habits for the current user
        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]

        if not rows:
            return [], []

        today = date.today()

        # get the streaks for all habits for the current user
        streak_map = Habit.streaks_by_user(user.user_id)

        due, optional = [], []

        # create a template to use for each habit
        for r in rows:
            hid  = r["habitID"]
            name = r["HabitName"]
            streak = int(streak_map.get(hid, 0))

            # fallback for error handling
            try:
                eq_days = max(1, int(r.get("EqualsToDays") or 1))
            except (TypeError, ValueError):
                eq_days = 1

            last_checked = r.get("LastChecked")

            # fallback for error handling
            try:
                last_dt = last_checked if isinstance(last_checked, datetime) else (datetime.fromisoformat(str(last_checked)) if last_checked else None)
            except Exception:
                last_dt = None

            # basis for the output 
            # Habitname, habitID and the streak
            label_tuple = (name, hid, streak) 

            # daily habits which are checked today shouldnt show up under optional again
            window_start = today - timedelta(days = eq_days - 1)

            if last_dt is None or last_dt.date() < window_start:
                due.append(label_tuple)
            else:
                if eq_days > 1 and last_dt.date() < today:
                    optional.append(label_tuple)

        return due, optional

    @output
    @render.ui
    def habits_display():
        """
        returns the div for the output including due habits & optional habits
        builds up on the tuple generated in _habits_for_home()
        """
        due, optional = _habits_for_home()

        if not due and not optional:
            return ui.p("Currently no habits to check. Check your list of habits under the 'EDIT HABITS' - screen.")
        
        due_choices = {str(hid): f"{name} (current streak: {streak})" for (name, hid, streak) in due}
        opt_choices = {str(hid): f"{name} (current streak: {streak})" for (name, hid, streak) in optional}

        return ui.div(
            ui.card(
                ui.h4(f"Do these today to keep your streak ({len(due)})"),
                ui.input_checkbox_group("home_due", None, choices=due_choices, selected=None, inline=False),
            ),
            ui.card(
                ui.h4(f"Optional today ({len(optional)})"),
                ui.input_checkbox_group("home_opt", None, choices=opt_choices, selected=None, inline=False),
            ),
            ui.input_action_button("home_mark_done", "Mark selected as done"),
        )

    @reactive.Effect
    @reactive.event(input.home_mark_done)
    def _mark_done():
        """
        handles the click on the button to Mark the selected habits as done
        """
        user = state()["current_user"]
        if user is None:
            return

        # if the user clicks the button without anything checked
        selected = set(input.home_due() or []) | set(input.home_opt() or [])
        if not selected:
            ui.notification_show("Nothing selected.", type="warning")
            return

        ids = [int(x) for x in selected]

        errors = []
        for hid in ids:
            try:
                mark_habit_as_checked(hid)
            except Exception as e:
                errors.append((hid, str(e)))

        ui.update_checkbox_group("home_due", selected=[])
        ui.update_checkbox_group("home_opt", selected=[])
        refresh_habits.set(refresh_habits() + 1)

        if errors:
            ui.notification_show(
                f"Saved with {len(errors)} error(s): {errors[:3]}",
                type="warning"
            )


    @reactive.Effect
    @reactive.event(input.user_selection)
    def home_go_sel():
        """
        handles the button to go back to the user selection
        """
        update_state(
            current_user=None,
            current_page="user_selection"
        )

    @reactive.Effect
    @reactive.event(input.edit_habits, ignore_init=True)
    def home_go_edit():
        """
        handles the button click on edit habits
        """
        update_state(current_page="edit_habits")

    @reactive.Effect
    @reactive.event(input.analyze_habits, ignore_init=True)
    def home_go_analyze():
        """
        handles the button click on analyze habits
        """
        update_state(current_page="analyze_habits")

