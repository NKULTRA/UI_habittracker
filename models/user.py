"""
Script handles the user class with some pre-defined methods
Methods mainly are wrapper for the database functions in database.py
"""

from services.database import get_users, new_user, delete_user, get_active_habits
from models.habit import Habit

class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

    @property
    def habits(self):
        """
        get active habits from the current user
        """
        rows = get_active_habits(self.user_id) or []
        return [Habit.from_row(r) for r in rows]

    @classmethod
    def get_all(cls):
        """
        get all users from the database
        """
        return [cls(user_id, username) for (user_id, username) in get_users()]

    @classmethod
    def create(cls, username):
        """
        Write new user to the database
        """
        user_id = new_user(username)
        return cls(user_id, username)

    def delete(self):
        """
        delete the current user
        """
        delete_user(self.user_id)
