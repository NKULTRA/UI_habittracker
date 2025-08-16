import pytest
from datetime import date, timedelta

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Suppose you have Habit.current_streak(check_dates, equal_days, today)
from models.habit import Habit

@pytest.mark.parametrize(
    "check_days,equal_days,today,created_date,expected",
    [
        ([], 1, date(2025,8,16),date(2025,8,16), 0),
        ([date(2025,8,16)], 1, date(2025,8,16),date(2025,8,16), 1),
        ([date(2025,8,15), date(2025,8,16)], 1, date(2025,8,16),date(2025,8,15), 2),
        ([date(2025,8,1), date(2025,8,8), date(2025,8,15)], 7, date(2025,8,16),date(2025,8,1), 3),
        ([date(2025,8,1), date(2025,8,12)], 7, date(2025,8,20), date(2025,8,1), 0),
    ],
)
def test_current_streak(check_days, equal_days, today, created_date, expected):
    s = Habit.current_streak(
        check_dates=check_days,
        equal_days=equal_days,
        today=today,
        created_date=created_date
    )
    assert s == expected
