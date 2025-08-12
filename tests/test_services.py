
import sqlite3, csv, pathlib, pytest, pandas as pd
from services.database import setup_database 

FIXTURES = pathlib.Path(__file__).parents[1] / "data" / "fixtures"

@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    setup_database(conn)            
    _seed_from_csvs(conn)
    yield conn
    conn.close()

def _seed_from_csvs(conn):
    def load_csv(name):
        with open(FIXTURES / name, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    cur = conn.cursor()
    for row in load_csv("users.csv"):
        cur.execute(
            "INSERT INTO user(userID, Username, DateCreated) VALUES (?, ?, ?)",
            (row["userID"], row["Username"], row["DateCreated"])
        )
    for row in load_csv("periodtypes.csv"):
        cur.execute(
            "INSERT INTO periodtypes(periodtypeID, Name) VALUES (?, ?)",
            (row["periodtypeID"], row["Name"])
        )
    for row in load_csv("habits.csv"):
        cur.execute(
            """INSERT INTO habits(habitID, userID, periodtypeID, HabitName,
               DateCreated, LastChecked, IsActive)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (row["habitID"], row["userID"], row["periodtypeID"], row["HabitName"],
             row["DateCreated"], row["LastChecked"] or None, row["IsActive"])
        )
    for row in load_csv("activities.csv"):
        cur.execute(
            "INSERT INTO activities(activityID, habitID, ActivityDate, IsChecked) VALUES (?, ?, ?, ?)",
            (row["activityID"], row["habitID"], row["ActivityDate"], row["IsChecked"])
        )
    conn.commit()
