import pandas as pd
from datetime import date

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.habit import Habit


#-----------Methods from analytical module--------------
def dl_active_habits(rows):
    df = pd.DataFrame(rows)

    return df[df["IsActive"] == 1]


def available_periods(rows):

    df = pd.DataFrame(rows)

    periods = sorted(df["Periodtype"].dropna().unique().tolist())

    return periods


def dl_periodicity(rows, period):

    df = pd.DataFrame(rows) 
    filtered_df = df[df["Periodtype"] == period] 

    if filtered_df is None or filtered_df.empty:
        filtered_df = pd.DataFrame(columns=[
            "habitID","userID","HabitName","periodtypeID","IsActive",
            "DateCreated","LastChecked","Periodtype","EqualsToDays"
        ])

    return filtered_df


def dl_archived_records(habits, checks_map, equal_days):

    rows = []
    df = pd.DataFrame(habits)
    arch = df[df["IsActive"] == 0]

    for a in arch.itertuples(index=False): 
        hid = a.habitID
        name = a.HabitName

        s = Habit.highest_streak(
            check_dates=sorted(set(checks_map.get(hid, []))),
            equal_days=equal_days,
        )

        rows.append({
            "habitID": hid,
            "HabitName": name,
            "EqualsToDays": equal_days,
            "record_streak": int(s or 0),
        })

    return pd.DataFrame(rows).sort_values(["HabitName", "habitID"]).reset_index(drop=True)


def dl_completions(habits, checks_map):

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
    return df


def dl_longest_overall(habits, checks_map, equal_days):

    rows = []
    for a in habits:
        hid = a["habitID"]
        name = a.get("HabitName")

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
    return top


def dl_longest_for_habit(rows, selected_habit, equal_days, checks_map):

    meta = next((r for r in rows if r.get("HabitName") == selected_habit), None) 

    hid = meta["habitID"]
    checks = checks_map[hid]
    streak = int(Habit.highest_streak(check_dates=sorted(set(checks)), equal_days=equal_days) or 0)
    print(streak)

    df = pd.DataFrame([{
        "habitID": hid,
        "HabitName": selected_habit,
        "EqualsToDays": equal_days,
        "record_streak": streak,
    }])
    
    return df


today = date(2025, 8, 16)
rows = [
        {
            "habitID": 1, 
            "userID": 1, 
            "HabitName": "Daily Run",
            "periodtypeID": 1, 
            "IsActive": 1,
            "DateCreated": "2025-07-01",
            "LastChecked": "2025-08-11",
            "Periodtype": "Daily", 
            "EqualsToDays": 1,
        },
        {
            "habitID": 2, 
            "userID": 1, 
            "HabitName": "Read Book",
            "periodtypeID": 2, 
            "IsActive": 1,
            "DateCreated": "2025-07-11",
            "LastChecked": "2025-08-08",
            "Periodtype": "Weekly", 
            "EqualsToDays": 7,
        },
        {
            "habitID": 3, 
            "userID": 1, 
            "HabitName": "Meditation",
            "periodtypeID": 3, 
            "IsActive": 0,
            "DateCreated": "2025-07-25",
            "LastChecked": "2025-08-03",
            "Periodtype": "every 10 days", 
            "EqualsToDays": 10,
        }
    ]
      
    
checks_map = {
        1: [date(2025,8,14), date(2025,8,15), date(2025,8,16)],        
        2: [date(2025,7,26), date(2025,8,2), date(2025,8,9)],    
        3: [date(2025,7,17), date(2025,7,27), date(2025,8,6)]    
    }


# ---------- Tests ----------
def test_dl_active_habits():
    df = dl_active_habits(rows)
    assert set(df["HabitName"]) == {"Daily Run", "Read Book"}
    assert (df["IsActive"] == 1).all()


def test_available_periods():
    periods = available_periods(rows)
    assert periods == ["Daily", "Weekly", "every 10 days"]


def test_dl_periodicity():
    df = dl_periodicity(rows, "Weekly")

    assert df.iloc[0]["HabitName"] == "Read Book"
    assert df.iloc[0]["Periodtype"] == "Weekly"


def test_dl_archived_records():
    df = dl_archived_records(rows, checks_map, equal_days=10)

    assert list(df["HabitName"]) == ["Meditation"]
    assert list(df["EqualsToDays"]) == [10]
    assert list(df["record_streak"]) == [3]


def test_dl_completions():
    df = dl_completions(rows, checks_map)
    assert df.shape == (3, 3)
    assert df["check_count"].tolist() == [3, 3, 3] 


def test_dl_longest_overall():
    df = dl_longest_overall(rows, checks_map, equal_days=10)

    assert df.shape == (1, 4)
    assert df.iloc[0]["HabitName"] == "Meditation"
    assert df.iloc[0]["record_streak"] == 3


def test_dl_longest_for_habit():
    df = dl_longest_for_habit(rows, selected_habit="Read Book", equal_days=7, checks_map=checks_map)
    assert df.iloc[0]["HabitName"] == "Read Book"
    assert df.iloc[0]["EqualsToDays"] == 7
    assert df.iloc[0]["record_streak"] == 3