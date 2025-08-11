from services.database import get_active_habits, get_habit, add_habit, edit_habit, delete_habit, get_archived_habits


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
