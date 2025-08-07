from services.database import add_entry, 
class Habit:
    def __init__(self, habit_id, user_id, name, period, is_active, last_checked=None):
        self.habit_id = habit_id
        self.user_id = user_id
        self.name = name
        self.period = period
        self.is_active = is_active
        self.last_checked = last_checked
    

    def to_dict(self):
        return {
            "habitID": self.habit_id,
            "HabitName": self.name,
            "Period": self.period,
            "IsActive": self.is_active,
            "LastChecked": self.last_checked
        }

    @staticmethod
    def get_by_user(user_id):
        rows = your_db_logic.get_habits_by_user(user_id)
        return [Habit(**row) for row in rows]

    @staticmethod
    def create(user_id, name, period, is_active=True):
        add_entry(user_id, name, period, is_active)

    @staticmethod
    def update(habit_id, **kwargs):
        your_db_logic.update_habit(habit_id, **kwargs)

    def delete(self):
        your_db_logic.delete_habit(self.habit_id)

