"""
Database layer. SQLite is the single source of truth for the app.
Every write here is parameterized (no string-built SQL) to avoid injection.
"""
import sqlite3
import os
from contextlib import contextmanager
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fitness.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER,
                sex TEXT,
                height_cm REAL,
                weight_kg REAL,
                goal_weight_kg REAL,
                activity_level TEXT,
                goal TEXT,
                timeline_weeks INTEGER,
                calorie_target INTEGER,
                protein_target INTEGER,
                water_target_ml INTEGER DEFAULT 2500,
                step_target INTEGER DEFAULT 8000,
                units TEXT DEFAULT 'kg',
                theme TEXT DEFAULT 'light',
                ai_enabled INTEGER DEFAULT 1,
                onboarded INTEGER DEFAULT 0,
                start_weight_kg REAL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS weight_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                note TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                food_name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                source TEXT DEFAULT 'manual',
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS custom_foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                serving TEXT,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS saved_meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                calories REAL NOT NULL,
                protein REAL NOT NULL,
                carbs REAL DEFAULT 0,
                fat REAL DEFAULT 0,
                ingredients TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                sets INTEGER,
                reps INTEGER,
                duration_min REAL,
                calories_est REAL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS water_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL,
                amount_ml INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS step_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL UNIQUE,
                steps INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL UNIQUE,
                sleep_hours REAL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS mood_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date TEXT NOT NULL UNIQUE,
                mood INTEGER,
                energy INTEGER,
                notes TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                weight_kg REAL NOT NULL,
                achieved INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


# ---------- generic helpers (all scoped by user_id -> no cross-user leaks) ----------

def fetch_all(query, params=()):
    with get_conn() as c:
        return [dict(r) for r in c.execute(query, params).fetchall()]


def fetch_one(query, params=()):
    with get_conn() as c:
        r = c.execute(query, params).fetchone()
        return dict(r) if r else None


def execute(query, params=()):
    with get_conn() as c:
        cur = c.execute(query, params)
        return cur.lastrowid


# ---------- profile ----------

def get_profile(user_id):
    return fetch_one("SELECT * FROM profiles WHERE user_id = ?", (user_id,))


def upsert_profile(user_id, **fields):
    existing = get_profile(user_id)
    if existing:
        sets = ", ".join(f"{k} = ?" for k in fields)
        execute(f"UPDATE profiles SET {sets} WHERE user_id = ?", (*fields.values(), user_id))
    else:
        cols = ", ".join(["user_id"] + list(fields.keys()))
        placeholders = ", ".join(["?"] * (len(fields) + 1))
        execute(f"INSERT INTO profiles ({cols}) VALUES ({placeholders})", (user_id, *fields.values()))


# ---------- weight ----------

def add_weight(user_id, weight_kg, log_date=None, note=""):
    log_date = log_date or str(date.today())
    execute(
        "INSERT INTO weight_logs (user_id, log_date, weight_kg, note) VALUES (?, ?, ?, ?)",
        (user_id, log_date, weight_kg, note),
    )


def get_weights(user_id):
    return fetch_all(
        "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY log_date ASC", (user_id,)
    )


def update_weight_log(log_id, weight_kg, note=""):
    execute("UPDATE weight_logs SET weight_kg = ?, note = ? WHERE id = ?", (weight_kg, note, log_id))


def delete_weight_log(log_id):
    execute("DELETE FROM weight_logs WHERE id = ?", (log_id,))


# ---------- meals ----------

def add_meal(user_id, food_name, calories, protein, carbs=0, fat=0, log_date=None, source="manual"):
    log_date = log_date or str(date.today())
    execute(
        """INSERT INTO meals (user_id, log_date, food_name, calories, protein, carbs, fat, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, log_date, food_name, calories, protein, carbs, fat, source),
    )


def get_meals(user_id, log_date=None):
    if log_date:
        return fetch_all(
            "SELECT * FROM meals WHERE user_id = ? AND log_date = ? ORDER BY id DESC", (user_id, log_date)
        )
    return fetch_all("SELECT * FROM meals WHERE user_id = ? ORDER BY log_date DESC, id DESC", (user_id,))


def delete_meal(meal_id):
    execute("DELETE FROM meals WHERE id = ?", (meal_id,))


def update_meal(meal_id, **fields):
    sets = ", ".join(f"{k} = ?" for k in fields)
    execute(f"UPDATE meals SET {sets} WHERE id = ?", (*fields.values(), meal_id))


# ---------- custom foods ----------

def add_custom_food(user_id, name, serving, calories, protein, carbs=0, fat=0):
    execute(
        """INSERT INTO custom_foods (user_id, name, serving, calories, protein, carbs, fat)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, serving, calories, protein, carbs, fat),
    )


def get_custom_foods(user_id):
    return fetch_all("SELECT * FROM custom_foods WHERE user_id = ? ORDER BY name", (user_id,))


# ---------- saved meals (recipes) ----------

def add_saved_meal(user_id, name, calories, protein, carbs, fat, ingredients):
    execute(
        """INSERT INTO saved_meals (user_id, name, calories, protein, carbs, fat, ingredients)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, calories, protein, carbs, fat, ingredients),
    )


def get_saved_meals(user_id):
    return fetch_all("SELECT * FROM saved_meals WHERE user_id = ? ORDER BY name", (user_id,))


# ---------- exercise ----------

def add_exercise_log(user_id, exercise_name, sets=None, reps=None, duration_min=None, calories_est=0, log_date=None):
    log_date = log_date or str(date.today())
    execute(
        """INSERT INTO exercise_logs (user_id, log_date, exercise_name, sets, reps, duration_min, calories_est)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, log_date, exercise_name, sets, reps, duration_min, calories_est),
    )


def get_exercise_logs(user_id, log_date=None):
    if log_date:
        return fetch_all(
            "SELECT * FROM exercise_logs WHERE user_id = ? AND log_date = ? ORDER BY id DESC", (user_id, log_date)
        )
    return fetch_all("SELECT * FROM exercise_logs WHERE user_id = ? ORDER BY log_date DESC", (user_id,))


def delete_exercise_log(log_id):
    execute("DELETE FROM exercise_logs WHERE id = ?", (log_id,))


# ---------- water / steps / sleep / mood ----------

def add_water(user_id, amount_ml, log_date=None):
    log_date = log_date or str(date.today())
    execute("INSERT INTO water_logs (user_id, log_date, amount_ml) VALUES (?, ?, ?)", (user_id, log_date, amount_ml))


def get_water_today(user_id, log_date=None):
    log_date = log_date or str(date.today())
    rows = fetch_all("SELECT amount_ml FROM water_logs WHERE user_id = ? AND log_date = ?", (user_id, log_date))
    return sum(r["amount_ml"] for r in rows)


def set_steps(user_id, steps, log_date=None):
    log_date = log_date or str(date.today())
    execute(
        """INSERT INTO step_logs (user_id, log_date, steps) VALUES (?, ?, ?)
           ON CONFLICT(log_date) DO UPDATE SET steps = excluded.steps""",
        (user_id, log_date, steps),
    )


def get_steps(user_id, days=7):
    return fetch_all(
        "SELECT * FROM step_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT ?", (user_id, days)
    )


def set_sleep(user_id, sleep_hours, log_date=None):
    log_date = log_date or str(date.today())
    execute(
        """INSERT INTO sleep_logs (user_id, log_date, sleep_hours) VALUES (?, ?, ?)
           ON CONFLICT(log_date) DO UPDATE SET sleep_hours = excluded.sleep_hours""",
        (user_id, log_date, sleep_hours),
    )


def get_sleep(user_id, days=7):
    return fetch_all(
        "SELECT * FROM sleep_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT ?", (user_id, days)
    )


def set_mood(user_id, mood, energy, notes="", log_date=None):
    log_date = log_date or str(date.today())
    execute(
        """INSERT INTO mood_logs (user_id, log_date, mood, energy, notes) VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(log_date) DO UPDATE SET mood=excluded.mood, energy=excluded.energy, notes=excluded.notes""",
        (user_id, log_date, mood, energy, notes),
    )


def get_mood(user_id, days=30):
    return fetch_all(
        "SELECT * FROM mood_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT ?", (user_id, days)
    )


# ---------- milestones ----------

def add_milestone(user_id, weight_kg):
    execute("INSERT INTO milestones (user_id, weight_kg, achieved) VALUES (?, ?, 0)", (user_id, weight_kg))


def get_milestones(user_id):
    return fetch_all("SELECT * FROM milestones WHERE user_id = ? ORDER BY weight_kg", (user_id,))


def mark_milestone_achieved(milestone_id):
    execute("UPDATE milestones SET achieved = 1 WHERE id = ?", (milestone_id,))


# ---------- distinct log dates (for streaks / calendar) ----------

def get_logged_dates(user_id):
    """Union of dates the user logged anything (meal, exercise, or weight)."""
    with get_conn() as c:
        rows = c.execute(
            """
            SELECT log_date FROM meals WHERE user_id = ?
            UNION
            SELECT log_date FROM exercise_logs WHERE user_id = ?
            UNION
            SELECT log_date FROM weight_logs WHERE user_id = ?
            """,
            (user_id, user_id, user_id),
        ).fetchall()
        return sorted({r["log_date"] for r in rows})
