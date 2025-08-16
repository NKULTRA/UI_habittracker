"""
Script handles the database setup
"""
from config import DB_PATH

import sqlite3
import re
from datetime import datetime
from collections import defaultdict


def setup_database():
    """
    Create all tables for the habittracker application if they don't exist
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON;")

        # create user table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                userID INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE NOT NULL,
                DateCreated TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        """)

        # create habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habitID INTEGER PRIMARY KEY AUTOINCREMENT,
                userID INTEGER NOT NULL,
                periodtypeID INTEGER NOT NULL,
                HabitName TEXT NOT NULL,
                DateCreated TIMESTAMP DEFAULT (datetime('now','localtime')),
                LastChecked TIMESTAMP,
                IsActive BOOLEAN DEFAULT 1,
                FOREIGN KEY (userID) REFERENCES user(userID),
                FOREIGN KEY (periodtypeID) REFERENCES periodtypes(periodtypeID),
                UNIQUE(userID, HabitName)
            )
        """)

        # create periodtypes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS periodtypes (
                periodtypeID INTEGER PRIMARY KEY AUTOINCREMENT,
                Periodtype TEXT UNIQUE NOT NULL,
                EqualsToDays INTEGER NOT NULL
            )
        """)

        # create activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                activityID INTEGER PRIMARY KEY AUTOINCREMENT,
                habitID INTEGER NOT NULL,
                ActivityDate TIMESTAMP DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (habitID) REFERENCES habits(habitID),
                UNIQUE(habitID, ActivityDate)
            )
        """)

        # ---------create indices for faster lookups---------------
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habits_user_active
            ON habits(userID, IsActive)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_habits_periodtype
            ON habits(periodtypeID)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_periodtypes_eqdays
            ON periodtypes(EqualsToDays)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activities_habit_date
            ON activities(habitID, ActivityDate)
        """)

        conn.commit()


# ----------------- helper functions -------------------
def _normalize_period(period_str):
    """
    When the user specifies a period as free text number, 
    this function converts it into a normalized label and 
    its equivalent in days for use in the periodtypes table

    Parameters:
    - period_str: string, period entered by the user
    """
    if bool(re.fullmatch(r"\d+", period_str.strip())):
        n = int(period_str)
        return (f"every {n} days", n)
    
    else:
        if period_str == "Daily":
            return ("Daily", 1)
        if period_str == "Weekly":
            return ("Weekly", 7)
        # monthly and yearly are normalized to 30 and 365
        if period_str == "Monthly":
            return ("Monthly", 30)
        if period_str == "Yearly":
            return ("Yearly", 365)

    # fallback when there is some form of error
    return ("Daily", 1)


def get_or_create_periodtype(period_label, equals_to_days):
    """
    Returns periodtypeID for a given label or 
    creates it if missing

    Parameters:
    - period_label: string, name of the selected period (e.g. Daily, Custom, etc.)
    - equals_to_days: integer, number of days which represent this period (e.g. Daily = 1)
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT periodtypeID 
            FROM periodtypes 
            WHERE Periodtype = ?
        """, (period_label,))

        row = cursor.fetchone()

        if row:
            return row["periodtypeID"]

        cursor.execute("""
            INSERT INTO periodtypes (Periodtype, EqualsToDays) 
            VALUES (?, ?)
        """, (period_label, equals_to_days))
        conn.commit()

        return cursor.lastrowid


# ------------------ user specific methods -------------------
def new_user(user_name):
    """
    Create a new user in the database

    Parameters:
    - user_name: str, the name the user enters
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO user
                    (UserName)
            VALUES (?)
        """, (user_name, ))

        conn.commit()

        return cursor.lastrowid


def delete_user(user_id):
    """
    Delete a user and all related habits

    Parameters:
    - user_id: integer, ID of the user to delete
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM habits 
            WHERE userID = ?
        """, (user_id,))
        
        cursor.execute("""
            DELETE FROM user 
            WHERE userID = ?
        """, (user_id,))
        
        conn.commit()


def user_exists(username):
    """
    Check whether a username is already in the database

    Parameters:
    - user_name: str, the name the user enters
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                1 
            FROM 
                user 
            WHERE 
                Username = ?
        """, (username,))
        
        return cursor.fetchone() is not None
    

def get_users():
    """
    Get all users that already exist
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                userID,
                Username
            FROM
                user
        """)

        results = cursor.fetchall()

        return results


# ------------ start of habit specific methods -------------

def add_habit(user_id, habit_name, period_str, is_active):
    """
    Adds a row to the habits table

    Parameters:
    - user_id: integer, ID of the current user
    - habit_name: string, Name of the habit
    - period_str: string, Period of the habit
    - is_active: boolean, active or archived - in theory the user can add new archived habits
    """
    label, days = _normalize_period(period_str)
    periodtype_id = get_or_create_periodtype(label, days)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO habits (userID, periodtypeID, HabitName, IsActive, LastChecked)
            VALUES (?, ?, ?, ?, NULL)
        """, (user_id, periodtype_id, habit_name, int(is_active)))
        hid = cursor.lastrowid

        conn.commit()
        return hid


def edit_habit(habit_id, habit_name, period_str, is_active):
    """
    When the user wants to edit a habit, this means updating one or more of
    its attributes in the habits table. Optionally, existing activities linked
    to the habit can be removed if its configuration changes.

    Parameters:
    - habit_id: integer, ID of the habit
    - habitname: string, old or edited name
    - period_str: string, old or edited period
    - is_active: integer, either archived = 0 or active = 1
    """
    label, days = _normalize_period(period_str)
    periodtype_id = get_or_create_periodtype(label, days)

    with sqlite3.connect(DB_PATH) as conn:

        cursor = conn.execute("""
                SELECT HabitName, periodtypeID, IsActive
                FROM habits
                WHERE habitID = ?
            """,(habit_id,))

        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Habit {habit_id} not found")

        old_name, old_periodtype_id, old_active = row

        structural = (habit_name != old_name) or (periodtype_id != old_periodtype_id)
        status_only = (not structural) and (is_active != old_active)

        # No effective change
        if not structural and not status_only:
            return get_habit(habit_id)

        if structural:
            try:
                conn.execute(
                    """
                    UPDATE habits
                    SET HabitName = ?, periodtypeID = ?, IsActive = ?, LastChecked = NULL
                    WHERE habitID = ?
                    """,
                    (habit_name, periodtype_id, int(is_active), habit_id),
                )
            except sqlite3.IntegrityError as e:
                # UNIQUE(userID, HabitName) violation most likely
                raise ValueError(f"Habit name '{habit_name}' already exists for this user.") from e

            conn.execute("""
                    DELETE FROM activities 
                    WHERE habitID = ?
                """,(habit_id,))

        else:
            # Only status changed (archive/unarchive)
            conn.execute("""
                UPDATE habits 
                SET IsActive = ? 
                WHERE habitID = ?
            """,(is_active, habit_id))

        return get_habit(habit_id)
    

def delete_habit(habit_id):
    """
    When the user wants to delete a habit completely from the database.
    All activities related to the habit will also be deleted

    Parameters:
    - habit_id: integer, ID of the habit
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
                DELETE FROM activities 
                WHERE habitID = ?
            """, (habit_id,))
        
        cursor.execute("""
                    DELETE FROM habits 
                    WHERE habitID = ?
                """, (habit_id,))
        
        conn.commit()


def get_habit(habit_id):
    """
    When the application needs the complete details of a single habit

    Parameters:
    - habit_id: integer, ID of the habit
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                h.habitID, 
                h.userID, 
                h.HabitName, 
                h.periodtypeID,
                h.DateCreated, 
                h.LastChecked, 
                h.IsActive,
                pt.Periodtype, 
                pt.EqualsToDays
            FROM habits h
              JOIN periodtypes pt ON h.periodtypeID = pt.periodtypeID
            WHERE h.habitID = ?
        """, (habit_id,))

        row = cursor.fetchone()

        return dict(row) if row else None


def get_active_habits(user_id):
    """
    Return all habit rows joined with periodtypes
    so a Habit object can be built

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                h.habitID,
                h.userID,
                h.HabitName,
                h.periodtypeID,
                h.DateCreated,
                h.LastChecked,
                h.IsActive,
                pt.Periodtype,
                pt.EqualsToDays
            FROM habits h
            JOIN periodtypes pt ON h.periodtypeID = pt.periodtypeID
            WHERE h.userID = ? AND h.IsActive = 1
            ORDER BY h.DateCreated, h.habitID
        """, (user_id,))

        return [dict(r) for r in cursor.fetchall()]


def get_archived_habits(user_id):
    """
    Get all archived habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                h.habitID,
                h.userID,
                h.HabitName,
                h.periodtypeID,
                h.DateCreated,
                h.LastChecked,
                h.IsActive,
                pt.Periodtype,
                pt.EqualsToDays
            FROM habits h
            JOIN periodtypes pt ON h.periodtypeID = pt.periodtypeID
            WHERE h.userID = ? AND h.IsActive = 0
            ORDER BY h.DateCreated, h.habitID
        """, (user_id,))

        return [dict(r) for r in cursor.fetchall()]


def mark_habit_as_checked(habit_id):
    """
    Records a completion/check for 'now' and updates LastChecked on the habit
    
    Parameters:
    - habit_id: integer, ID of the selected habit
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO activities (habitID, ActivityDate)
            VALUES (?, ?)
        """, (habit_id, now))

        cursor.execute("""
            UPDATE habits
            SET LastChecked = ?
            WHERE habitID = ?
        """, (now, habit_id))

        conn.commit()


def get_checks_for_habits(habit_id_list):
    """
    Get all checks for a habit
    
    Parameters:
    - habit_id_list: list, array of various habit ids for which the checks need to be known
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT 
                habitID, 
                DATE(ActivityDate) AS date
            FROM activities
            WHERE habitID IN ({",".join(["?"] * len(habit_id_list))})
            GROUP BY habitID, date
            ORDER BY habitID, date DESC
            """,
            habit_id_list,
        )

        out = defaultdict(list)
        for row in cursor.fetchall():
            out[row["habitID"]].append(row["date"])

        return {hid: out.get(hid, []) for hid in habit_id_list}