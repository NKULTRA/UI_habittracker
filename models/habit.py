from services.database import get_active_habits, get_habit, add_habit, edit_habit, delete_habit, get_archived_habits, mark_habit_as_checked, get_checks_for_habits
from datetime import date, datetime, timedelta


class Habit:
    def __init__(self, habit_id, user_id, habit_name, periodtype_id, is_active = 1, 
                 date_created = None, last_checked = None, period_label = None, equals_days = None):
        self.habit_id = habit_id
        self.user_id = user_id
        self.habit_name = habit_name
        self.periodtype_id = periodtype_id
        self.is_active = int(is_active)
        self.date_created = date_created
        self.last_checked = last_checked
        self.period_label = period_label
        self.equals_days = equals_days


    @staticmethod
    def from_row(row):
        return Habit(
            habit_id=row["habitID"],
            user_id=row["userID"],
            habit_name=row["HabitName"],
            periodtype_id=row["periodtypeID"],
            is_active=row["IsActive"],
            date_created=row.get("DateCreated"),
            last_checked=row.get("LastChecked"),
            period_label=row.get("Periodtype"),
            equals_days=row.get("EqualsToDays"),
        )

    def to_dict(self):
        return {
            "habitID": self.habit_id,
            "userID": self.user_id,
            "HabitName": self.habit_name,
            "periodtypeID": self.periodtype_id,
            "IsActive": self.is_active,
            "DateCreated": self.date_created,
            "LastChecked": self.last_checked,
            "Periodtype": self.period_label,
            "EqualsToDays": self.equals_days,
        }

    @staticmethod
    def full_list_by_user(user_id):
        rows = get_active_habits(user_id)
        rows += get_archived_habits(user_id)
        
        return [Habit.from_row(r) for r in rows]

    @staticmethod
    def list_by_user(user_id):
        rows = get_active_habits(user_id)
        return [Habit.from_row(r) for r in rows]

    @staticmethod
    def get(habit_id):
        row = get_habit(habit_id)
        return Habit.from_row(row) if row else None

    @staticmethod
    def create(user_id: int, habit_name, period_str, is_active):
        new_id = add_habit(user_id, habit_name, period_str, is_active)
        return Habit.get(new_id)

    def update(self, habit_name, period_str, is_active):

        edit_habit(
            self.habit_id,
            habit_name=habit_name,
            period_str=period_str,
            is_active=is_active
        )

        updated = Habit.get(self.habit_id)
        return updated

    def delete(self):
        delete_habit(self.habit_id)


    def mark_checked(self):
        mark_habit_as_checked(self.habit_id)
      
    @classmethod
    def ongoing_streaks_by_user(cls, user_id):

        habits = get_active_habits(user_id)

        if not habits:
            return {}

        habit_ids = [h["habitID"] for h in habits]
        checks_map = get_checks_for_habits(habit_ids)
        today = date.today()

        out = {}

        for h in habits:
            hid = str(h["habitID"])

            days = int(h["EqualsToDays"])
            checks = checks_map.get(hid, [])
            out[hid] = cls.current_streak(
                check_dates=checks,
                equal_days=days,        
                today=today,
                include_current_window_only_if_checked=True,
            )
        return out

    @staticmethod
    def _to_date(d):
        if d is None:
            return None
        if isinstance(d, date) and not isinstance(d, datetime):
            return d
        return datetime.fromisoformat(str(d)).date()

    @staticmethod
    def current_streak(check_dates, equal_days, today, include_current_window_only_if_checked):

        days = sorted({Habit._to_date(d) for d in check_dates if Habit._to_date(d) is not None}, reverse=True)
        if not days:
            return 0

        streak = 0
        window_end = today

        while True:
            window_start = window_end - timedelta(days = equal_days - 1)
            has_check = any(window_start <= d <= window_end for d in days)

            if not has_check:
                if streak == 0 and not include_current_window_only_if_checked:
                    return 1
                break

            streak += 1
            window_end = window_start - timedelta(days=1)

        return streak
    
    @staticmethod
    def highest_streak(check_dates, equal_days):
        """

        """

        days = sorted({Habit._to_date(d) for d in check_dates if Habit._to_date(d) is not None})

        if not days:
            return 0

        min_day = days[0]
        window_end = days[-1]  

        best = 0
        cur = 0

        while window_end >= min_day:
            window_start = window_end - timedelta(days=equal_days - 1)

            has_check = any(window_start <= d <= window_end for d in days)
            if has_check:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0

            window_end = window_start - timedelta(days=1)

        return best