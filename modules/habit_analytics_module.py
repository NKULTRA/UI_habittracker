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
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates


def habit_analytics_ui():
    return ui.page_fluid(
        ui.layout_columns(
            # plot on the left side
            ui.card(
                {"class": "analytics-plot"},
                ui.h4("Streaks over time (active habits)"),
                ui.output_plot("streaks_plot")
            ),

            # buttons on the right side
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
        loads the active habits from the current user and returns them as a list of dict
        """
        user = state()["current_user"]

        if user is None:
            return []
        return [h.to_dict() for h in Habit.list_by_user(user.user_id)]

    @reactive.Calc
    def _streak_history_df():
        """
        calculates the streak history for the plot for all active habits
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
            # calculate the streak for every check that happened
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
        """
        sets up the plot on the left side of the UI
        """
        df = _streak_history_df()
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No streak data yet", ha="center", va="center")
            ax.axis("off")
            return fig

        df = df.copy()

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["HabitName", "date"])

        n_dates = df["date"].nunique()

        # calculations to have some benchmarks for the axis sizes, depending on the number of checks / streak
        if n_dates <= 20:
            k = n_dates                  
        elif n_dates <= 60:
            k = 30                    
        elif n_dates <= 150:
            k = 60                       
        else:
            k = 90                  

        last_unique = np.sort(df["date"].unique())[-k:]
        df = df[df["date"].isin(last_unique)]

        # plot
        fig, ax = plt.subplots()

        habits = df["HabitName"].unique()
        jitter_amount = 0.15 

        for _, name in enumerate(habits):
            g = df[df["HabitName"] == name]
            jitter = np.random.uniform(-jitter_amount, jitter_amount, size=len(g))
            ax.plot(g["date"], g["streak"] + jitter, marker="o", label=name, linestyle='-')


        max_streak = int(df["streak"].max())
        upper = max_streak + 3
        ax.set_ylim(0, max(upper, 1))
        # control the axis ticks automatically and nicely, so that they are readable  
        ax.yaxis.set_major_locator(MaxNLocator(integer=True)) 

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
        fig.autofmt_xdate()

        ax.legend(loc="best")
        ax.grid(True, axis="y", linestyle=":", linewidth=0.8)

        return fig


    @output()
    @render.download(filename="active_habits.csv")
    def dl_active_habits():
        rows = _active_habits_rows()
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
            "habitID","userID","HabitName","periodtypeID","IsActive",
            "DateCreated","LastChecked","Periodtype","EqualsToDays"
        ])

        yield df.to_csv(index=False).encode("utf-8")


    @output()
    @render.download(filename="streak_history.csv")
    def dl_streak_history():
        df = _streak_history_df()
        yield df.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")


    @reactive.Effect
    @reactive.event(input.analytics_home)
    def analyze_go_home():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")
