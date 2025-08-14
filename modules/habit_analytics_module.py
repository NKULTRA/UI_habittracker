"""
Module creates the Analyze Habits Screen
after the user clicks the button on the home screen
"""
from shiny import render, ui, reactive, req
from services.state import state, update_state
from models.habit import Habit
from services.database import get_checks_for_habits
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
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
                ui.div(
                    {"class": "alert alert-custom d-flex align-items-center mb-2", "role": "alert"},
                    "Download buttons are active only when there’s something to download."
                ),
                ui.output_ui("active_habits_button"),
                ui.output_ui("periodicity_button"),
                ui.output_ui("archived_records_button"),
                ui.output_ui("completions_button"),
                ui.output_ui("longest_overall_button"),
                ui.output_ui("longest_habit_button"),
                ui.br(),
                ui.input_action_button("analytics_home", "Back to the home screen")
            )
        )
    )


def habit_analytics_server(input, output, session):

    @reactive.Calc
    def _streak_history_df():
        """
        calculates the streak history for the plot for all active habits
        """
        user = state()["current_user"] 
        rows = [h.to_dict() for h in Habit.list_by_user(user.user_id)]
        if not rows:
            return pd.DataFrame(columns=["date", "habitID", "HabitName", "streak"])

        habit_ids = [r["habitID"] for r in rows]
        checks_map = get_checks_for_habits(habit_ids) 

        out = []
        for r in rows:
            hid = r["habitID"]
            name = r["HabitName"]

            try:
                equal_days = int(r.get("EqualsToDays") or 1)
            except (TypeError, ValueError):
                equal_days = 1

            checks = checks_map.get(hid, [])
                
            if not checks:
                continue

            days = sorted({Habit._to_date(d) for d in checks if Habit._to_date(d) is not None})

            # calculate the streak for every check that happened
            # broken flags are not collected here
            for d in days:
                s, _broken = Habit.current_streak(
                    check_dates=days,
                    equal_days=equal_days,
                    today=d,
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

        df["date"] = pd.to_datetime(df["date"]).dt.normalize() 
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

        # Plot
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
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        n_days = df["date"].nunique()
        interval = max(1, n_days // 8)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
        ax.xaxis.set_minor_locator(ticker.NullLocator()) 
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%d"))
        fig.autofmt_xdate(rotation=0)

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

        if df.empty:
            df = pd.DataFrame(columns=["habitID","HabitName","IsActive","DateCreated","LastChecked","Periodtype","EqualsToDays"])

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
        req(input.analyze_habit_period())

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
    @render.ui
    def archived_records_button():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.archived_list_by_user(user.user_id)]

        if not rows:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_archived_records", "Archived + record streaks", disabled = True, style = "width:100%;")),
                ui.column(10),
            )

        return ui.layout_columns(
                ui.column(10, ui.download_button("dl_archived_records", "Archived + record streaks", style = "width:100%;")),
                ui.column(10),
        )
    
    @output
    @render.download(filename="archived_with_record_streaks.csv")
    def dl_archived_records():
        user = state()["current_user"]
        arch = [h.to_dict() for h in Habit.archived_list_by_user(user.user_id)]

        if not arch:
            yield _as_csv_bytes(pd.DataFrame(columns=["habitID","HabitName","EqualsToDays","record_streak"]))
            return

        habit_ids = [a["habitID"] for a in arch]
        checks_map = get_checks_for_habits(habit_ids)

        rows = []
        for a in arch:
            hid = a["habitID"]
            name = a.get("HabitName")
            try:
                equal_days = max(1, int(a.get("EqualsToDays") or 1))
            except (TypeError, ValueError):
                equal_days = 1

            s = Habit.highest_streak(
                check_dates=sorted(set(checks_map.get(hid, []))),
                equal_days=equal_days
            )

            rows.append({
                "habitID": hid,
                "HabitName": name,
                "EqualsToDays": equal_days,
                "record_streak": int(s or 0),
            })

        df = pd.DataFrame(rows).sort_values(["HabitName","habitID"])
        yield _as_csv_bytes(df)


    @output
    @render.ui
    def completions_button():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        if not rows:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_completions", "Completions per habit", disabled = True, style = "width:100%;")),
                ui.column(10),
            )

        return ui.layout_columns(
                    ui.column(10, ui.download_button("dl_completions", "Completions per habit", style = "width:100%;")),
                    ui.column(10),
        )

    @output
    @render.download(filename="completions_per_habit.csv")
    def dl_completions():
        user = state()["current_user"]

        habits = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        if not habits:
            yield _as_csv_bytes(pd.DataFrame(columns=["habitID", "HabitName", "check_count"]))
            return

        habit_ids = [a["habitID"] for a in habits]
        checks_map = get_checks_for_habits(habit_ids)

        rows = []
        for a in habits:
            hid = a["habitID"]
            checks = checks_map.get(hid, []) or []
            rows.append({
                "habitID": hid,
                "HabitName": a.get("HabitName"),
                "check_count": len(checks),
            })

        df = pd.DataFrame(rows).sort_values(["HabitName", "habitID"])
        yield _as_csv_bytes(df)


    @output
    @render.ui
    def longest_overall_button():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        if not rows:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_longest_overall", "Longest run (overall)", disabled = True, style = "width:100%;")),
                ui.column(10),
            )
        
        return ui.layout_columns(
                    ui.column(10, ui.download_button("dl_longest_overall", "Longest run (overall)", style = "width:100%;")),
                    ui.column(10),
        )

    @output
    @render.download(filename="longest_run_overall.csv")
    def dl_longest_overall():
        user = state()["current_user"]
        habits = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        if not habits:
            yield _as_csv_bytes(pd.DataFrame(columns=["habitID","HabitName","EqualsToDays","record_streak"]))
            return

        habit_ids = [a["habitID"] for a in habits]
        checks_map = get_checks_for_habits(habit_ids)

        rows = []
        for a in habits:
            hid = a["habitID"]
            name = a.get("HabitName")
            try:
                equal_days = max(1, int(a.get("EqualsToDays") or 1))
            except (TypeError, ValueError):
                equal_days = 1

            s = Habit.highest_streak(
                check_dates=sorted(set(checks_map.get(hid, []))),
                equal_days=equal_days
            )

            rows.append({
                "habitID": hid,
                "HabitName": name,
                "EqualsToDays": equal_days,
                "record_streak": int(s or 0),
            })

        df = pd.DataFrame(rows)
        top = df.sort_values(["record_streak", "HabitName", "habitID"],
                            ascending=[False, True, True]).head(1)
        yield _as_csv_bytes(top)

    @output
    @render.ui
    def longest_habit_button():
        user = state()["current_user"]
        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]

        if not rows:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_longest_for_habit", "Longest run (selected habit)", disabled = True, style = "width:100%;")),
                ui.column(10, ui.input_select("analyze_habit_record", label=None, choices=[])),
            )
        
        habit_ids = [a["habitID"] for a in rows]
        checks_map = get_checks_for_habits(habit_ids)
        
        if not checks_map:
            return ui.layout_columns(
                ui.column(10, ui.input_action_button("dl_longest_for_habit", "Longest run (selected habit)", disabled = True, style = "width:100%;")),
                ui.column(10, ui.input_select("analyze_habit_record", label=None, choices=[])),
            )

        df = pd.DataFrame(rows)
        habits = sorted(df["HabitName"].dropna().unique().tolist())

        return ui.layout_columns(
            ui.column(10, ui.download_button("dl_longest_for_habit", "Longest run (selected habit)", style = "width:100%;")),
            ui.column(10, ui.input_select("analyze_habit_record", label=None, choices=habits)),
        )
    
    @output
    @render.download(filename="longest_run_selected_habit.csv")
    def dl_longest_for_habit():
        req(input.analyze_habit_record())

        sel_habit = input.analyze_habit_record()
        user = state()["current_user"]

        rows = [h.to_dict() for h in Habit.full_list_by_user(user.user_id)]
        meta = next((r for r in rows if r.get("HabitName") == sel_habit), None)
        if not meta:
            yield _as_csv_bytes(pd.DataFrame(columns=["habitID","HabitName","EqualsToDays","record_streak"]))
            return

        hid = meta["habitID"]
        equal_days = int(meta.get("EqualsToDays") or 1)

        checks = get_checks_for_habits([hid]).get(hid, [])
        streak = int(Habit.highest_streak(check_dates=sorted(set(checks)), equal_days=equal_days) or 0)

        df = pd.DataFrame([{
            "habitID": hid,
            "HabitName": sel_habit,
            "EqualsToDays": equal_days,
            "record_streak": streak,
        }])
        yield _as_csv_bytes(df)


    @reactive.Effect
    @reactive.event(input.analytics_home)
    def analyze_go_home():
        """
        handles the button click to go back to the home screen
        """
        update_state(current_page="home_screen")
