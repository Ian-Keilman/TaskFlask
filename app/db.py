import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Return one SQLite connection for the current request."""
    if "db" not in g:
        db = sqlite3.connect(current_app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        g.db = db

    return g.db


def close_db(error=None):
    """Close the request's database connection, if one was opened."""
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Reset the database from schema.sql."""
    db = get_db()
    schema_path = Path(current_app.root_path).parent / "schema.sql"

    with schema_path.open("r", encoding="utf-8") as schema_file:
        db.executescript(schema_file.read())
    db.commit()


def migrate_db():
    """Apply non-destructive schema additions to an existing database."""
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'To Do',
            priority TEXT NOT NULL DEFAULT 'Medium',
            story_points INTEGER NOT NULL DEFAULT 1 CHECK (story_points IN (1, 2, 3, 5, 8, 13, 21, 34, 55, 89)),
            assignee TEXT,
            due_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (sprint_id) REFERENCES sprints (id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_activity_log_entity
            ON activity_log(entity_type, entity_id);
        """
    )

    task_columns = {
        row["name"] for row in db.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "story_points" not in task_columns:
        db.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN story_points INTEGER NOT NULL DEFAULT 1
                CHECK (story_points IN (1, 2, 3, 5, 8, 13, 21, 34, 55, 89))
            """
        )

    tasks_schema = db.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'tasks'"
    ).fetchone()["sql"]
    if "21, 34, 55, 89" not in tasks_schema:
        db.executescript(
            """
            ALTER TABLE tasks RENAME TO tasks_old_story_points;

            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sprint_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'To Do',
                priority TEXT NOT NULL DEFAULT 'Medium',
                story_points INTEGER NOT NULL DEFAULT 1
                    CHECK (story_points IN (1, 2, 3, 5, 8, 13, 21, 34, 55, 89)),
                assignee TEXT,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (sprint_id) REFERENCES sprints (id) ON DELETE CASCADE
            );

            INSERT INTO tasks (
                id, sprint_id, title, description, status, priority,
                story_points, assignee, due_date, created_at, updated_at
            )
            SELECT
                id, sprint_id, title, description, status, priority,
                story_points, assignee, due_date, created_at, updated_at
            FROM tasks_old_story_points;

            DROP TABLE tasks_old_story_points;
            """
        )

    db.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_tasks_sprint_id ON tasks(sprint_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON tasks(assignee);
        """
    )
    db.commit()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """CLI command used by `flask --app run init-db`."""
    init_db()
    click.echo("Initialized the TaskFlask database.")


@click.command("migrate-db")
@with_appcontext
def migrate_db_command():
    """CLI command used by `flask --app run migrate-db`."""
    migrate_db()
    click.echo("Migrated the TaskFlask database.")