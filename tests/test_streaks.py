import pytest
import pandas as pd
from datetime import date, timedelta
from pandas.testing import assert_frame_equal

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.habit import Habit

@pytest.mark.parametrize(
    "check_days,equal_days,today,expected",
    [
        ([], 1, date(2025,8,16), 0),
        ([date(2025,8,16)], 1, date(2025,8,16), 1),
        ([date(2025,8,15), date(2025,8,16)], 1, date(2025,8,16), 2),
        ([date(2025,8,1), date(2025,8,8), date(2025,8,15)], 7, date(2025,8,16), 3),
        ([date(2025,8,1), date(2025,8,12)], 7, date(2025,8,20), 0),
    ],
)

def test_current_streak(check_days, equal_days, today, expected):
    s = Habit.current_streak(
        check_dates=check_days,
        equal_days=equal_days,
        today=today
    )
    assert s == expected


def build_streak_history(equal_days, rows, today, checks_map):

    out = []

    # logic from the script
    for r in rows:
        hid = r["habitID"]
        name = r["HabitName"]
        created_date = r["DateCreated"]

        days = sorted({Habit._to_date(d) for d in checks_map})

        if days:
            start_date = days[0]
        elif created_date:
            start_date = created_date
        else:
            start_date = today

        min_start = today - timedelta(days=180 - 1)

        if start_date < min_start:
            start_date = min_start

        date_range = pd.date_range(start=start_date, end=today, freq="D")

        for d in date_range:
            s = Habit.current_streak(
                check_dates=days,
                equal_days=equal_days,
                today=d.date()
            )
            out.append({
                "date": pd.to_datetime(d.date()),
                "habitID": hid,
                "HabitName": name,
                "streak": int(s)
            })
    df = pd.DataFrame(out).sort_values(["HabitName", "date"])
    df["date"] = pd.to_datetime(df["date"])
    df["habitID"] = df["habitID"].astype(int)
    df["streak"] = df["streak"].astype(int)

    return df

def test_meditate():
    
    rows = [
        {
            "habitID": 1,
            "userID": 1,
            "HabitName": "Meditate",
            "periodtypeID": 4,
            "IsActive": 1,
            "DateCreated": "2025-07-01",
            "LastChecked": "2025-08-11",
            "Periodtype": "every 10 days",
            "EqualsToDays": 10,
        }
    ]

    checks_map = [date(2025,7,18), date(2025,7,26), date(2025,8,5), date(2025,8,11)]
    today = date(2025,8,11)

    df = build_streak_history(equal_days=10, rows=rows, today=today, checks_map=checks_map)

    expected = pd.DataFrame([
        {"date": pd.to_datetime("2025-07-18"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-19"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-20"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-21"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-22"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-23"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-24"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-25"), "habitID": 1, "HabitName": "Meditate", "streak": 1},
        {"date": pd.to_datetime("2025-07-26"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-07-27"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-07-28"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-07-29"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-07-30"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-07-31"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-08-01"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-08-02"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-08-03"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-08-04"), "habitID": 1, "HabitName": "Meditate", "streak": 2},
        {"date": pd.to_datetime("2025-08-05"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-06"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-07"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-08"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-09"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-10"), "habitID": 1, "HabitName": "Meditate", "streak": 3},
        {"date": pd.to_datetime("2025-08-11"), "habitID": 1, "HabitName": "Meditate", "streak": 4}
    ])

    assert_frame_equal(df.reset_index(drop=True), expected.reset_index(drop=True))