from sqlite3 import IntegrityError
from services.database import get_users, new_user, load_user_information

class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.habits = None

    @classmethod
    def get_all(cls):
        return [cls(user_id, username) for user_id, username in get_users()]

    @classmethod
    def load(cls, username):
        return [cls(user_id, username) for user_id, username in load_user_information(username)]

    @classmethod
    def create(cls, username):
        user_id = new_user(username)
        return cls(user_id, username)

