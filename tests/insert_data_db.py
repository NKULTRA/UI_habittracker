"""
This script writes the test files into the database
The app must be started at least once upfront to have 
"""

import sqlite3
import pandas as pd
from pathlib import Path


DB_PATH = "services/habittracker.db"

def setup_database(DB_PATH):
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


CSV = {
    "user":        "tests/testfiles/user.csv",   
    "periodtypes":  "tests/testfiles/periodtypes.csv", 
    "habits":       "tests/testfiles/habits.csv",  
    "activities":   "tests/testfiles/activities.csv",  
}

TABLE_META = {
    "user":       (["userID", "Username", "DateCreated"], "userID"),
    "periodtypes": (["periodtypeID", "Periodtype", "EqualsToDays"], "periodtypeID"),
    "habits":      (["habitID", "userID", "periodtypeID", "HabitName", "DateCreated", "LastChecked", "IsActive"], "habitID"),
    "activities":  (["activityID", "habitID", "ActivityDate"], "activityID"),
}

def connect():
    conn = sqlite3.connect(DB_PATH)
    return conn

def read_csv(path_str):
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")
    return pd.read_csv(p)

def insert_df(conn, table, df):
    table_cols, autoinc_col = TABLE_META[table]
    cols = [c for c in table_cols if c in df.columns]

    if autoinc_col in cols and autoinc_col not in df.columns:
        cols.remove(autoinc_col)

    if not cols:
        print(f"[WARN] No matching columns to insert for table '{table}'. Skipping.")
        return

    df2 = df.copy()
    df2 = df2.where(pd.notnull(df2), None)

    placeholders = ",".join(["?"] * len(cols))
    collist = ",".join(cols)
    sql = f"INSERT INTO {table} ({collist}) VALUES ({placeholders})"

    conn.executemany(sql, df2[cols].values.tolist())
    print(f"[OK] Inserted {len(df2)} rows into '{table}'.")

def main():
    conn = connect()
    try:
        with conn: 
            setup_database(DB_PATH)

            df_user = read_csv(CSV["user"])
            insert_df(conn, "user", df_user)

            df_periods = read_csv(CSV["periodtypes"])
            insert_df(conn, "periodtypes", df_periods)


            df_habits = read_csv(CSV["habits"])
            insert_df(conn, "habits", df_habits)

            df_acts = read_csv(CSV["activities"])
            insert_df(conn, "activities", df_acts)

        print("All done.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()








