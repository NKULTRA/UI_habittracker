"""
Script handles the database setup
"""
from config import DB_PATH

import sqlite3


def setup_database():
    """
    Create all tables for the habittracker application if they don't exist
    additionally a view for calculating the streaks
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
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # create habits table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habitID INTEGER PRIMARY KEY AUTOINCREMENT,
                userID INTEGER NOT NULL,
                periodtypeID INTEGER NOT NULL,
                HabitName TEXT NOT NULL,
                DateCreated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                activitytypeID INTEGER NOT NULL,
                ActivityDate TIMESTAMP,
                DateCreated TIMESTAMP,
                FOREIGN KEY (habitID) REFERENCES habits(habitID),
                FOREIGN KEY (activitytypeID) REFERENCES activitytypes(activitytypeID)
            )
        """)

        # create activitytypes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activitytypes (
                activitytypeID INTEGER PRIMARY KEY AUTOINCREMENT,
                ActivityName TEXT UNIQUE NOT NULL
            )
        """)

        # create a view for the streaks
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS streaks AS
                WITH ordered_checks AS (
                    SELECT
                        a.habitID,
                        a.ActivityDate,
                        pt.EqualsToDays,
                        ROW_NUMBER() OVER (
                            PARTITION BY a.habitID
                            ORDER BY a.ActivityDate DESC
                        ) AS rn,
                        LAG(a.ActivityDate) OVER (
                            PARTITION BY a.habitID
                            ORDER BY a.ActivityDate DESC
                        ) AS prev_check
                    FROM activities a
                    JOIN activitytypes at ON a.activitytypeID = at.activitytypeID
                    JOIN habits h ON a.habitID = h.habitID
                    JOIN periodtypes pt ON h.periodtypeID = pt.periodtypeID
                    WHERE at.ActivityName = 'check'
                ),
                streak_flags AS (
                    SELECT
                        habitID,
                        ActivityDate,
                        rn,
                        CASE
                            WHEN prev_check IS NULL THEN 1
                            WHEN JULIANDAY(prev_check) - JULIANDAY(ActivityDate) <= EqualsToDays
                            THEN 1 ELSE 0
                        END AS in_streak
                    FROM ordered_checks
                ),
                broken_streaks AS (
                    SELECT
                        habitID,
                        rn,
                        ActivityDate,
                        in_streak,
                        SUM(CASE WHEN in_streak = 0 THEN 1 ELSE 0 END)
                            OVER (PARTITION BY habitID ORDER BY rn) AS streak_group
                    FROM streak_flags
                )
            SELECT
                h.habitID,
                h.HabitName,
                u.Username,
                pt.Periodtype,
                COUNT(*) AS current_streak
            FROM broken_streaks bs
            JOIN habits h ON bs.habitID = h.habitID
            JOIN user u ON h.userID = u.userID
            JOIN periodtypes pt ON h.periodtypeID = pt.periodtypeID
            WHERE bs.streak_group = 0
            AND h.IsActive = 1
            GROUP BY h.habitID;
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
    if int(period_str):
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
    creates it if missing.
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
    

def user_information(user_id):
    """
    Get the username by the id 

    Parameters:
    - user_id: integer, the ID of the chosen user
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT userID, Username, DateCreated
            FROM user
            WHERE userID = ?
        """, (user_id,))

        row = cursor.fetchone()

        return dict(row) if row else None


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

def add_habit(user_id, habit_name, period_str, is_active = 1):
    """
    Adds a row to the given table.

    Parameters:
    - table: str, the table name
    - entry: dict, mapping of column names to values, e.g.
             {"HabitName": "Read", "Is_Active": 1, ...}
    """
    label, days = _normalize_period(period_str)
    periodtype_id = get_or_create_periodtype(label, days)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO habits (userID, periodtypeID, HabitName, IsActive)
            VALUES (?, ?, ?, ?)
        """, (user_id, periodtype_id, habit_name.strip(), int(is_active)))
        conn.commit()
        return cursor.lastrowid


def archive_habit(habit_id):
    """
    When the user wants to archive a habit, 
    this is equal to set IsActive = 0 in the habit table
    
    Parameters:
    - habit_id: integer, ID of the habit
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE habits 
            SET IsActive = 0
            WHERE habitID = ?
        """, (habit_id))

        conn.commit()


def edit_habit(user_id, habit_id, updates):
    """
    When the user wants to edit a habit, this means updating one or more of
    its attributes in the habits table. Optionally, existing activities linked
    to the habit can be removed if its configuration changes.

    Parameters:
    - user_id: integer, ID of the current user
    - habit_id: integer, ID of the habit
    - updates: dict, mapping of column names to new values, e.g.
               {"HabitName": "Read", "IsActive": 1, "periodtypeID": 2}
    """
    if not updates:
        return 0

    updates = dict(updates)

    period_changed = False
    allowed_cols = {"HabitName", "periodtypeID", "IsActive", "LastChecked"}

    return None


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
    so a Habit object can be built.

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


def get_habits_with_same_period(user_id, period):
    """
    Get all active habits with the same period from the
    current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.habitID, a.HabitName
            FROM habits a
            JOIN periodtypes b ON a.periodtypeID = b.periodtypeID
            WHERE a.userID = ? AND a.IsActive = 1 AND b.Periodtype = ?
        """, (user_id, period))

        return [dict(r) for r in cursor.fetchall()]


def get_archived_habits(user_id):
    """
    Get all archived habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT habitID, HabitName
            FROM habits
            WHERE userID = ? AND IsActive = 0
        """, (user_id,))
        return cursor.fetchall()
