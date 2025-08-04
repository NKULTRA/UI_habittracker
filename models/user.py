from services.database import user_information, get_users, new_user, get_active_habits, delete_user

class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self._habits = None

    @property
    def habits(self):
        if self._habits is None:
            self._habits = get_active_habits(self.user_id) or []
        return self._habits

    def refresh_habits(self):
        self._habits = get_active_habits(self.user_id) or []

    @classmethod
    def get_all(cls):
        return [cls(user_id, username) for user_id, username in get_users()]

    @classmethod
    def create(cls, username):
        user_id = new_user(username)
        return cls(user_id, username)

    @classmethod
    def load_by_id(cls, user_id):
        user_id, username = user_information(user_id)
        return cls(user_id, username)

    def delete(self):
        delete_user(self.user_id)

