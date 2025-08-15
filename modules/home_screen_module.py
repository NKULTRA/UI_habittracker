"""
Module creates the page after the login
The home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
from services.database import mark_habit_as_checked
from models.habit import Habit
from datetime import datetime, date


def home_screen_ui():
    return ui.page_fluid(
        ui.layout_columns(
            ui.div(
                {"class": "home-container"},
                # habits table on the left of the UI
                ui.card(
                    {"class": "home-table"},
                    ui.h4("Your Habits"),
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
        also it seperates into broken habits when within the last gap between today and the equal days of this habit is no check
        the created date doesnt play a role, because after creation the habit has its equal days to get a check
        """
        user = state()["current_user"]
        _ = refresh_habits()
        if user is None:
            return [], [], []

        # get habits for the current user
        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]
        if not rows:
            return [], [], []

        today = date.today()

        # current streaks + "broken now" flag (no check in current window)
        streak_map = Habit.ongoing_streaks_by_user(user.user_id)

        due, optional, broken = [], [], []

        for r in rows:
            hid  = r["habitID"]
            name = r["HabitName"]
            streak = int(streak_map.get(hid, 0))
            equal_days = int(r.get("EqualsToDays") or 1)
            last_checked = r.get("LastChecked")
            date_created = r.get("DateCreated")

            try:
                last_dt = last_checked if isinstance(last_checked, datetime) else (
                    datetime.fromisoformat(str(last_checked)) if last_checked else None
                )
            except Exception:
                last_dt = None

            try:
                created_dt = last_checked if isinstance(date_created, datetime) else (
                    datetime.fromisoformat(str(date_created)) if date_created else None
                )
            except Exception:
                created_dt = None

            has_check = last_dt is not None
            base_dt = last_dt or created_dt or datetime.combine(today, datetime.min.time())
            days_since = (today - base_dt.date()).days

            label = (name, hid, streak)

            if equal_days == 1:
                # daily habits
                if has_check:
                    if days_since <= 0:
                        # already checked today
                        continue
                    elif days_since == 1:
                        due.append(label)
                    else:
                        broken.append(label)
                else:
                    # never checked: daily is due immediately
                    due.append(label)
            else:
                # non daily
                if has_check:
                    if days_since <= 0:
                        # checked today
                        continue
                    elif 1 <= days_since <= equal_days - 2:
                        optional.append(label)
                    elif days_since in (equal_days - 1, equal_days):
                        due.append(label)
                    else:
                        broken.append(label)
                else:
                    # never checked: measure from creation
                    if days_since <= equal_days - 2:
                        optional.append(label)
                    elif days_since in (equal_days - 1, equal_days):
                        due.append(label)
                    else:
                        broken.append(label)

        return due, optional, broken


    @output
    @render.ui
    def habits_display():
        """
        returns the div for the output including due habits, optional and broken habits
        a habit is considered broken when there is no check in the last gap from today - days for this habit
        builds up on the tuple generated in _habits_for_home()
        """
        due, optional, broken = _habits_for_home()

        if not due and not optional and not broken:
            return  ui.div(
                {"class": "alert alert-custom", "role": "alert"},
                "Currently no habits to check. You can review your list under the “Edit Habits” screen."
            )
            
        due_choices = {str(hid): f"{name} (current streak: {streak})" for (name, hid, streak) in due}
        opt_choices = {str(hid): f"{name} (current streak: {streak})" for (name, hid, streak) in optional}
        broken_choices = {str(hid): f"{name} (current streak: {streak})" for (name, hid, streak) in broken}

        return ui.div(
            ui.div(
                {"class": "alert alert-custom", "role": "alert"},
                "Tip: Check the box to mark a habit complete, then click the button below to confirm."
            ),
            # due habits
            ui.card(
                ui.h4(f"Do these today to keep your streak ({len(due)})"),
                ui.input_checkbox_group("home_due", None, choices=due_choices, selected=None, inline=False),
            ),
            # optional habits
            ui.card(
                ui.h4(f"Optional today ({len(optional)})"),
                ui.input_checkbox_group("home_opt", None, choices=opt_choices, selected=None, inline=False),
            ),
            # broken habits
            ui.card(
                ui.h4(f"Broken habits ({len(broken)})"),
                ui.input_checkbox_group("home_broken", None, choices=broken_choices, selected=None, inline=False),
            ),
            # button at the bottom
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
                # write to the database
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

