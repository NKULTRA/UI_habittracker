"""
Script handles the habit class with some pre-defined methods
Methods mainly are wrapper for the database functions in database.py
"""
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
        """
        create habit object from database row

        Parameters:
        - row: list, a row of a habit from the database 
        """
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
        """
        make a dictionary from a habit, useful for most functions
        """
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
        """
        get all habits from the current user
        (active + archived ones)

        Parameters:
        - user_id: integer, ID of the current user
        """
        rows = get_active_habits(user_id)
        rows += get_archived_habits(user_id)
        
        return [Habit.from_row(r) for r in rows]

    @staticmethod
    def list_by_user(user_id):
        """
        get only active habits from the current user
        identical to the function in the user class
        the user class was mainly used on the home screen

        Parameters:
        - user_id: integer, ID of the current user
        """
        rows = get_active_habits(user_id)
        return [Habit.from_row(r) for r in rows]

    @staticmethod
    def archived_list_by_user(user_id):
        """
        get all archived habits from the current user

        Parameters:
        - user_id: integer, ID of the current user
        """
        rows = get_archived_habits(user_id)
        return [Habit.from_row(r) for r in rows]

    @staticmethod
    def get(habit_id):
        """
        get the information for one particular habit from its id
        returns a habit object

        Parameters:
        - habit_id: integer, ID of habit
        """
        row = get_habit(habit_id)
        return Habit.from_row(row) if row else None

    @staticmethod
    def create(user_id, habit_name, period_str, is_active):
        """
        write a new habit to the database

        Parameters:
        - user_id: integer, ID of the current user
        - habit_name: string, Name of the Habit to create
        - period_str: string, period of the habit
        - is_active: boolean, archived or active habit
        """
        new_id = add_habit(user_id, habit_name, period_str, is_active)
        return Habit.get(new_id)


    def update(self, habit_name, period_str, is_active):
        """
        for the edit habit selection, overwrites the old information

        Parameters:
        - user_id: integer, ID of the current user
        - habit_name: string, Name of the Habit to create
        - period_str: string, period of the habit
        - is_active: boolean, archived or active habit
        """
        edit_habit(
            self.habit_id,
            habit_name=habit_name,
            period_str=period_str,
            is_active=is_active
        )

        updated = Habit.get(self.habit_id)
        return updated

    def delete(self):
        """
        delete the selected habit
        """
        delete_habit(self.habit_id)


    def mark_checked(self):
        """
        mark the selected habit as checked and write the date to the database
        """
        mark_habit_as_checked(self.habit_id)
      
    @classmethod
    def ongoing_streaks_by_user(cls, user_id):
        """
        calculate the current, ongoing streaks for one user

        Parameters:
        - user_id: integer, ID of the current user
        """
        habits = get_active_habits(user_id)

        if not habits:
            return {}

        habit_ids = [h["habitID"] for h in habits]
        checks_map = get_checks_for_habits(habit_ids)
        today = date.today()

        out = {}

        for h in habits:
            hid = h["habitID"]

            days = int(h["EqualsToDays"])
            checks = checks_map.get(hid, [])
            streak = cls.current_streak(
                check_dates=checks,
                equal_days=days,        
                today=today,
                created_date=h["DateCreated"]
            )
            out[hid] = streak

        return out

    @staticmethod
    def _to_date(d):
        """
        helper function to return a data
        
        Parameters:
        - d: string / date, a string or a date to check or format to date
        """
        if d is None:
            return None
        if isinstance(d, date) and not isinstance(d, datetime):
            return d
        return datetime.fromisoformat(str(d)).date()

    @staticmethod
    def current_streak(check_dates, equal_days, today, created_date):
        """
        calculate the current streak for a habit

        Parameters:
        - check_dates: dict, key: habit_id, value: check dates for the habit
        - equal_days: integer, the value in days for the habit
        - today: date, the date of today
        - created_date: string, the date of the habit created from the database
        """
        days = sorted([Habit._to_date(d) for d in check_dates if Habit._to_date(d) is not None])
        if not days:
            return 0
        
        if (today - days[-1]).days > equal_days:
            return 0

        streak = 0
        end = today
        i = len(days) - 1

        while i >= 0:
            while i >= 0 and days[i] > end:
                i -= 1
            if i < 0:
                break

            window_start = end - timedelta(days=equal_days - 1)
            if days[i] < window_start:
                break
            streak += 1

            end = days[i] - timedelta(days=1)
            i -= 1

        return streak
                
    
    @staticmethod
    def highest_streak(check_dates, equal_days):
        """
        calculate the highest ever streak a habit had

        Parameters:
        - check_dates: dict, key: habit_id, value: check dates for the habit
        - equal_days: integer, the value in days for the habit
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