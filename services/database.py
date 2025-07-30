"""
Script handles the database setup
"""
import sqlite3

def setup_database():
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
            lastChecked TIMESTAMP,
            isActive BOOLEAN DEFAULT 1,
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