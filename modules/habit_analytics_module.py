"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import render, ui, reactive
from services.state import state, update_state
from models.habit import Habit
from services.database import get_checks_for_habits
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


def habit_analytics_ui():
    return ui.page_fluid(
        ui.layout_columns(

            ui.card(
                {"class": "analytics-plot"},
                ui.h4("Streaks over time (active habits)"),
                ui.output_plot("streaks_plot")
            ),

            ui.card(
                {"class": "analytics-downloads"},
                ui.h4("Downloads"),
                ui.p("Export CSVs based on your current data:"),
                ui.download_button("dl_active_habits", "Active habits (CSV)"),
                ui.download_button("dl_streak_history", "Streak history (CSV)"),
                ui.br(),
                ui.input_action_button("analytics_home", "Back to the home screen")
            ),
        )
    )


def habit_analytics_server(input, output, session):


    @reactive.Calc
    def _active_habits_rows():
        """
        Active habits as list[dict]. Expects Habit.list_by_user() to include
        Periodtype and EqualsToDays via the join to periodtypes.
        """
        user = state()["current_user"]
        if user is None:
            return []
        return [h.to_dict() for h in Habit.list_by_user(user.user_id)]

    @reactive.Calc
    def _streak_history_df():
        """
        One row per habit per CHECK day:
        columns: ["date", "habitID", "HabitName", "streak"]
        Streak is computed as of that day.
        """
        rows = _active_habits_rows()
        if not rows:
            return pd.DataFrame(columns=["date", "habitID", "HabitName", "streak"])

        habit_ids = [r["habitID"] for r in rows]
        checks_map = get_checks_for_habits(habit_ids) 

        out = []
        for r in rows:
            hid = r["habitID"]
            name = r["HabitName"]

            try:
                eq_days = max(1, int(r.get("EqualsToDays") or 1))
            except (TypeError, ValueError):
                eq_days = 1

            days = sorted(set(checks_map.get(hid, [])))
            for d in days:
                s = Habit.current_streak(
                    check_dates=checks_map.get(hid, []),
                    eq_days=eq_days,
                    today=datetime.fromisoformat(str(d)).date(),
                    include_current_window_only_if_checked=True,
                )
                out.append({"date": pd.to_datetime(d), "habitID": hid, "HabitName": name, "streak": int(s)})

        if not out:
            return pd.DataFrame(columns=["date", "habitID", "HabitName", "streak"])

        df = pd.DataFrame(out).sort_values(["HabitName", "date"])
        return df


    @output
    @render.plot
    def streaks_plot():
        df = _streak_history_df()
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No streak data yet", ha="center", va="center")
            ax.axis("off")
            return fig

        fig, ax = plt.subplots()
        for name, g in df.groupby("HabitName"):
            ax.plot(g["date"], g["streak"], marker="o", label=name)

        ax.set_xlabel("Date")
        ax.set_ylabel("Streak")
        ax.set_title("Streaks over time")
        ax.legend(loc="best")
        fig.autofmt_xdate()
        return fig


    @render.download
    def dl_active_habits():
        """
        CSV of active habits (one row per habit).
        """
        rows = _active_habits_rows()
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
            "habitID","userID","HabitName","periodtypeID","IsActive",
            "DateCreated","LastChecked","Periodtype","EqualsToDays"
        ])

        def writer():
            yield df.to_csv(index=False).encode("utf-8")

        return render.Download("active_habits.csv", writer)

    @render.download
    def dl_streak_history():
        """
        CSV of streak history (one row per check day per habit).
        """
        df = _streak_history_df()

        def writer():
            yield df.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")

        return render.Download("streak_history.csv", writer)


    @reactive.Effect
    @reactive.event(input.analytics_home)
    def analyze_go_home():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")
