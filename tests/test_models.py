import pytest, sqlite3

def test_unique_habit_per_user(conn):
    cur = conn.cursor()
    # Try to insert duplicate HabitName for same user -> should fail
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute(
            "INSERT INTO habits(userID, periodtypeID, HabitName, IsActive) VALUES (1, 1, ?, 1)",
            ("Drink water",)
        )

def test_archive_vs_edit(conn):
    cur = conn.cursor()
    # Simulate "edit" by archiving old and creating new
    cur.execute("UPDATE habits SET IsActive=0 WHERE habitID=1")
    cur.execute(
        "INSERT INTO habits(userID, periodtypeID, HabitName, IsActive) VALUES (1,1,?,1)",
        ("Drink water (v2)",)
    )
    conn.commit()
    count_active = cur.execute("SELECT COUNT(*) FROM habits WHERE IsActive=1 AND userID=1").fetchone()[0]
    assert count_active >= 1
