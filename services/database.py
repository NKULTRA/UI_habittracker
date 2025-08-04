"""
Script handles the database setup
"""
from config import DB_PATH

import sqlite3


def setup_database():
    """
    Create all tables for the habittracker application if they don't exist.
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
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                userID,
                Username
            FROM
                user
        """)

        results = cursor.fetchone()
            
        return results


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


def add_entry(table, entry):
    """
    Adds a row to the given table.

    Parameters:
    - table: str, the table name
    - entry: dict, mapping of column names to values, e.g.
             {"HabitName": "Read", "Is_Active": 1, ...}
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        columns = ", ".join(entry.keys())
        placeholders = ", ".join(["?"] * len(entry))
        values = tuple(entry.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        conn.commit()


def archive_entry(user_id, habit_name):
    """
    When the user wants to archive a habit, 
    this is equal to set IsActive = 0 in the habit table
    
    Parameters:
    - user_id: integer, ID of the current user
    - habit_name: string, Name of the habit
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE habits 
            SET IsActive = 0
            WHERE userID = ? AND HabitName = ?
        """, (user_id, habit_name))

        conn.commit()


def edit_entry(user_id, habit_id, updates):
    """
    When the user wants to edit a habit
    
    Parameters:
    - user_id: integer, ID of the current user
    - habit_id: integer, ID of the habit
    - updates: dict, mapping of column names to new values, e.g.
             {"HabitName": "Read", ...}
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # delete all old activities
        cursor.execute("""
            DELETE FROM activities 
                WHERE habitID = ?
        """, (habit_id,))

        # build update query
        columns = ", ".join([f"{col} = ?" for col in updates.keys()])
        values = list(updates.values()) + [habit_id, user_id]

        cursor.execute(
            f"""UPDATE habits 
            SET {columns} 
            WHERE habitID = ? 
            AND userID = ?
            """, values)

        conn.commit()


def get_active_habits(user_id):
    """
    Get all active habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                HabitName
            FROM
                habits
            WHERE
                userID = ? AND
                IsActive = 1
        """, (user_id,))

        results = [row[0] for row in cursor.fetchall()]

        return results


def get_habits_with_same_period(user_id, period):
    """
    Get all active habits with the same period from the
    current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
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

        return results


def get_archived_habits(user_id):
    """
    Get all archived habits of the current user

    Parameters:
    - user_id: integer, ID of the current user
    """
    with sqlite3.connect(DB_PATH) as conn:
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

        return results


def get_numbr_checks():
    pass


def get_longest_streak():
    pass


def get_longest_streak(user_id, habit_id):
    pass
