"""
Script handles the database setup
"""
import sqlite3


def setup_database():
    """
    Create all tables for the habittracker application if they don't exist.
    """
    conn = sqlite3.connect("habittracker.db")
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


def add_entry(table, entry):
    """
    Adds a row to the given table.

    Parameters:
    - table: str, the table name
    - entry: dict, mapping of column names to values, e.g.
             {"HabitName": "Read", "Is_Active": 1, ...}
    """
    conn = sqlite3.connect("habittracker.db")
    cursor = conn.cursor()
    
    # Extract column names and values
    columns = ", ".join(entry.keys())
    placeholders = ", ".join(["?"] * len(entry))
    values = tuple(entry.values())

    # Build and execute query
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
    conn = sqlite3.connect("habittracker.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE habits 
        SET IsActive = 1
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
    conn = sqlite3.connect("habittracker.db")
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


def get_longest_streak():
    pass


def get_longest_streak(habit_id):
    pass


def get_active_habits():
    pass


def get_habits_with_same_period():
    pass


def get_archived_habits():
    pass


def get_numbr_checks():
    pass