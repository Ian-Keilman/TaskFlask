from datetime import datetime, timezone

from .db import get_db


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def list_projects():
    """
    Return all projects, newest updated first.

    Sprint 1 only needs a basic project list.
    """
    return get_db().execute(
        """
        SELECT *
        FROM projects
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()


def get_project(project_id):
    """
    Return one project by id.

    Used for project detail, edit, and delete.
    """
    return get_db().execute(
        """
        SELECT *
        FROM projects
        WHERE id = ?
        """,
        (project_id,),
    ).fetchone()


def create_project(name, description):
    """
    Create a new project.

    Sprint 1 includes basic project creation.
    """
    timestamp = _now()

    cursor = get_db().execute(
        """
        INSERT INTO projects (name, description, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, timestamp, timestamp),
    )

    get_db().commit()
    return cursor.lastrowid


def update_project(project_id, name, description):
    """
    Update an existing project.

    Sprint 1 includes editing project information.
    """
    get_db().execute(
        """
        UPDATE projects
        SET name = ?, description = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, description, _now(), project_id),
    )

    get_db().commit()


def delete_project(project_id):
    """
    Delete a project.

    Sprint 1 includes basic project deletion.
    """
    get_db().execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
        (project_id,),
    )

    get_db().commit()
    