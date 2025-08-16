# load_csvs_into_sqlite.py
import sqlite3
import pandas as pd
from pathlib import Path


DB_PATH = "services/habittracker.db"

CSV = {
    "user":        "tests/testfiles/user.csv",        # columns e.g.: userID?, Username
    "periodtypes":  "tests/testfiles/periodtypes.csv",  # columns e.g.: Periodtype, EqualsToDays
    "habits":       "tests/testfiles/habits.csv",       # columns e.g.: habitID?, userID, periodtypeID, HabitName, DateCreated?, LastChecked?, IsActive?
    "activities":   "tests/testfiles/activities.csv",   # columns e.g.: activityID?, habitID, ActivityDate?
}

# Table → (all columns in table, autoincrement PK column name)
TABLE_META = {
    "user":       (["userID", "Username", "DateCreated"], "userID"),
    "periodtypes": (["periodtypeID", "Periodtype", "EqualsToDays"], "periodtypeID"),
    "habits":      (["habitID", "userID", "periodtypeID", "HabitName", "DateCreated", "LastChecked", "IsActive"], "habitID"),
    "activities":  (["activityID", "habitID", "ActivityDate"], "activityID"),
}

def connect():
    conn = sqlite3.connect(DB_PATH)
    return conn

def read_csv(path_str: str) -> pd.DataFrame:
    p = Path(path_str)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")
    return pd.read_csv(p)

def insert_df(conn, table: str, df: pd.DataFrame):
    # Only insert columns that exist in both the CSV and the table.
    table_cols, autoinc_col = TABLE_META[table]
    cols = [c for c in table_cols if c in df.columns]

    # If autoincrement PK isn't provided in CSV, don't include it (let SQLite generate it).
    if autoinc_col in cols and autoinc_col not in df.columns:
        cols.remove(autoinc_col)

    if not cols:
        print(f"[WARN] No matching columns to insert for table '{table}'. Skipping.")
        return

    # Replace NaN with None so sqlite gets NULLs.
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
        with conn:  # single transaction

            # 1) user
            df_user = read_csv(CSV["user"])
            insert_df(conn, "user", df_user)

            # 2) periodtypes
            df_periods = read_csv(CSV["periodtypes"])
            insert_df(conn, "periodtypes", df_periods)

            # 3) habits
            df_habits = read_csv(CSV["habits"])
            insert_df(conn, "habits", df_habits)

            # 4) activities
            df_acts = read_csv(CSV["activities"])
            insert_df(conn, "activities", df_acts)

        print("All done.")
    finally:
        conn.close()

if __name__ == "__main__":

    main()








