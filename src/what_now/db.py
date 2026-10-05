# src/what_now/db.py
"""SQLite schema and helpers for tasks and action logs."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "whatnow.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    deadline TEXT,
    estimated_minutes INTEGER NOT NULL,
    energy_cost TEXT NOT NULL CHECK (energy_cost IN ('low', 'medium', 'high')),
    importance INTEGER NOT NULL CHECK (importance BETWEEN 1 AND 5),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    why TEXT NOT NULL,
    first_step TEXT NOT NULL,
    timebox_minutes INTEGER NOT NULL,
    fallback TEXT NOT NULL,
    outcome TEXT CHECK (outcome IN ('done', 'skip', 'blocked')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    """Open a connection with row access by column name and FK enforcement."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def list_active_tasks() -> list[dict]:
    """Return all tasks that haven't been completed yet."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE completed_at IS NULL ORDER BY deadline IS NULL, deadline ASC"
        ).fetchall()
    return [dict(row) for row in rows]


def add_task(title, deadline, estimated_minutes, energy_cost, importance) -> int:
    """Insert a task and return its id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO tasks (title, deadline, estimated_minutes, energy_cost, importance)
               VALUES (?, ?, ?, ?, ?)""",
            (title, deadline, estimated_minutes, energy_cost, importance),
        )
        return cur.lastrowid


def complete_task(task_id: int) -> None:
    """Mark a task done by stamping completed_at."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET completed_at = datetime('now') WHERE id = ?",
            (task_id,),
        )


def log_action(task_id, action: dict) -> int:
    """Save a suggested action. Returns its id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO actions
               (task_id, action, why, first_step, timebox_minutes, fallback)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                action["action"],
                action["why"],
                action["first_step"],
                action["timebox_minutes"],
                action["fallback"],
            ),
        )
        return cur.lastrowid


def record_outcome(action_id: int, outcome: str) -> None:
    """Update the outcome of a logged action. outcome must be done/skip/blocked."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE actions SET outcome = ? WHERE id = ?",
            (outcome, action_id),
        )