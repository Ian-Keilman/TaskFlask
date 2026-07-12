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