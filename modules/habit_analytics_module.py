"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import render, ui, reactive, req
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
                ui.h4("Download CSVs"),
                ui.output_ui("active_habits_button"),
                ui.output_ui("periodicity_button"),
                ui.layout_columns(
                    ui.output_ui("archived_records_button"),
                    ui.column(10, ui.download_button("dl_archived_records", "Archived + record streaks", style = "width:100%;")),
                    ui.column(10),
                ),
                ui.layout_columns(
                    ui.output_ui("completions_button"),
                    ui.column(10, ui.download_button("dl_completions", "Completions per habit", style = "width:100%;")),
                    ui.column(10),
                ),
                ui.layout_columns(
                    ui.output_ui("longest_overall_button"),
                    ui.column(10, ui.download_button("dl_longest_overall", "Longest run (overall)", style = "width:100%;")),
                    ui.column(10),
                ),
                ui.layout_columns(
                    ui.output_ui("longest_habit_button"),
                    ui.column(10, ui.download_button("dl_longest_for_habit", "Longest run (selected habit)", style = "width:100%;")),
                    ui.column(10,  ui.input_select("analyze_habit_record", label=None, choices=["test"])),
                ),
                ui.br(),
                ui.input_action_button("analytics_home", "Back to the home screen")
            )
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
                equal_days = max(1, int(r.get("EqualsToDays") or 1))
            except (TypeError, ValueError):
                equal_days = 1

            days = sorted(set(checks_map.get(hid, [])))
            # calculate the streak for every check that happened
            for d in days:
                s = Habit.current_streak(
                    check_dates=checks_map.get(hid, []),
                    equal_days=equal_days,
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

    def _as_csv_bytes(df):
        return df.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8")

    @output
    @render.ui
    def active_habits_button():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]

        if not rows:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_active_habits", "Active habits", disabled = True, style = "width:100%;")),
                ui.column(10),
            )

        return ui.layout_columns(
            ui.column(10, ui.download_button("dl_active_habits", "Active habits", style = "width:100%;")),
            ui.column(10),
        )
    
    
    @output
    @render.download(filename="active_habits.csv")
    def dl_active_habits():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]

        df = pd.DataFrame(rows)

        if df is None or df.empty:
            df = pd.DataFrame(columns=[
                "habitID","userID","HabitName","periodtypeID","IsActive",
                "DateCreated","LastChecked","Periodtype","EqualsToDays"
            ])

        yield _as_csv_bytes(df)

    @reactive.Calc
    def available_periods():
        user = state()["current_user"]

        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]
        if not rows:
            return []  
        
        df = pd.DataFrame(rows)

        periods = sorted(df["Periodtype"].dropna().unique().tolist())
        return periods
    

    @output
    @render.ui
    def periodicity_button():
        periods = available_periods()

        if not periods:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_periodicity", "Habits by periodicity", disabled = True, style = "width:100%;")),
                ui.column(10, ui.input_select("analyze_habit_period", label=None, choices=[], multiple=False)),
            )

        return ui.layout_columns(
            ui.column(10, ui.download_button("dl_periodicity", "Habits by periodicity", disabled = False, style = "width:100%;")),
            ui.column(10, ui.input_select("analyze_habit_period", label=None, choices=periods, multiple=False)),
        )

    @output
    @render.download(filename="habits_by_periodicity.csv")
    def dl_periodicity():
        req(available_periods())

        user = state()["current_user"]
        period = input.analyze_habit_period()
        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        df = pd.DataFrame(rows) 
        filtered_df = df[df["Periodtype"] == period]

        if filtered_df is None or filtered_df.empty:
            filtered_df = pd.DataFrame(columns=[
                "habitID","userID","HabitName","periodtypeID","IsActive",
                "DateCreated","LastChecked","Periodtype","EqualsToDays"
            ])

        yield _as_csv_bytes(filtered_df)

    @output
    @render.download(filename="archived_with_record_streaks.csv")
    def dl_archived_records():
        rows = _archived_record_streaks_rows(user_id)
        df = pd.DataFrame(rows) if not isinstance(rows, pd.DataFrame) else rows
        yield _as_csv_bytes(df if df is not None else pd.DataFrame())

    @output
    @render.download(filename="completions_per_habit.csv")
    def dl_completions():
        rows = _completions_per_habit_rows(user_id)
        df = pd.DataFrame(rows) if not isinstance(rows, pd.DataFrame) else rows
        yield _as_csv_bytes(df if df is not None else pd.DataFrame())

    @output
    @render.download(filename="longest_run_overall.csv")
    def dl_longest_overall():
        rows = _longest_run_overall_rows(user_id)
        df = pd.DataFrame(rows) if not isinstance(rows, pd.DataFrame) else rows
        yield _as_csv_bytes(df if df is not None else pd.DataFrame())

    @output
    @render.download(filename="longest_run_selected_habit.csv")
    def dl_longest_for_habit():
        raw = input.habit_id()
        if raw in (None, "", "None"):
            # No selection → export an empty frame with a hint
            df = pd.DataFrame({"message": ["No habit selected"]})
            yield _as_csv_bytes(df)
            return
        habit_id = int(raw)
        rows = _longest_run_for_habit_rows(user_id, habit_id)
        df = pd.DataFrame(rows) if not isinstance(rows, pd.DataFrame) else rows
        yield _as_csv_bytes(df if df is not None else pd.DataFrame())

########## hier darüber anpassen

    @reactive.Effect
    @reactive.event(input.analytics_home)
    def analyze_go_home():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")
