from sqlite3 import IntegrityError
from services.database import get_users, new_user

class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

    @classmethod
    def get_all(cls):
        return [cls(user_id, username) for user_id, username in get_users()]

    @classmethod
    def create(cls, username):
        try:
            user_id = new_user(username)
            return cls(user_id, username)
        except IntegrityError:
            print(f"⚠️ Username '{username}' already exists.")
            return None
