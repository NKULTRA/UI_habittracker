"""
Script handles the database setup
"""
from config import DB_PATH

import sqlite3


def setup_database():
    """
    Create all tables for the habittracker application if they don't exist.
    """
    conn = sqlite3.connect(DB_PATH)
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

    conn.commit()
    conn.close()


def new_user(user_name):
    """
    Create a new user in the database

    Parameters:
    - user_name: str, the name the user enters
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user
                   (UserName)
        VALUES (?)
    """, (user_name, ))

    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    return (user_id, user_name)


def load_user_information(user_id):
    """
    Get all information of the user, when it exists

    Parameters:
    - user_id: integer, the ID of the chosen user
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            userID
            Username
        FROM
            user
    """)

    results = cursor.fetchall()
    conn.close()

    return results


def get_users():
    """
    Get all users that already exist
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            userID,
            Username
        FROM
            user
    """)

    results = cursor.fetchall()
    conn.close()
    print(results)
    return results


def add_entry(table, entry):
    """
    Adds a row to the given table.

    Parameters:
    - table: str, the table name
    - entry: dict, mapping of column names to values, e.g.
             {"HabitName": "Read", "Is_Active": 1, ...}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns = ", ".join(entry.keys())
    placeholders = ", ".join(["?"] * len(entry))
    values = tuple(entry.values())

    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)

    conn.commit()
    conn.close()


def archive_entry(user_id, habit_name):
    """
    When the user wants to archive a habit, 
    this is equal to set IsActive = 0 in the habit table
    
    Parameters:
    - user_id: integer, ID of the current user
    - habit_name: string, Name of the habit
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE habits 
        SET IsActive = 0
        WHERE userID = ? AND HabitName = ?
    """, (user_id, habit_name))

    conn.commit()
    conn.close()


def edit_entry(user_id, habit_id, updates):
    """
    When the user wants to edit a habit
    
    Parameters:
    - user_id: integer, ID of the current user
    - habit_id: integer, ID of the habit
    - updates: dict, mapping of column names to new values, e.g.
             {"HabitName": "Read", ...}
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # delete all old activities
    cursor.execute("DELETE FROM activities WHERE habitID = ?", (habit_id,))

    # build update query
    columns = ", ".join([f"{col} = ?" for col in updates.keys()])
    values = list(updates.values()) + [habit_id, user_id]

    cursor.execute(
        f"UPDATE habits SET {columns} WHERE habitID = ? AND userID = ?",
        values
    )

    conn.commit()
    conn.close()


def get_active_habits(user_id):
    """
    Get all active habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            HabitName
        FROM
            habits
        WHERE
            userID = ? AND
            IsActive = 1
    """(user_id))

    results = [row[0] for row in cursor.fetchall()]
    conn.close()

    return results


def get_habits_with_same_period(user_id, period):
    """
    Get all active habits with the same period from the
    current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            a.HabitName
        FROM
            habits a LEFT JOIN periodtypes b
                ON a.periodtypeID = b.periodtypeID
        WHERE
            a.userID = ? AND
            a.IsActive = 1 AND
            b.Periodtype = ? 
    """(user_id, period))

    results = cursor.fetchall()
    conn.close()

    return results


def get_archived_habits(user_id):
    """
    Get all archived habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            HabitName
        FROM
            habits
        WHERE
            userID = ? AND
            IsActive = 0
    """(user_id))

    results = [row[0] for row in cursor.fetchall()]
    conn.close()

    return results


def get_numbr_checks():
    pass


def get_longest_streak():
    pass


def get_longest_streak(user_id, habit_id):
    pass
