import sqlite3
from pathlib import Path

import click
from flask import current_app, g


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


@click.command("init-db")
def init_db_command():
    """CLI command used by `flask --app run init-db`."""
    init_db()
    click.echo("Initialized the TaskFlask database.")
    