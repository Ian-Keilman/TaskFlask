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

def list_sprints(project_id):
    """Return all sprints for one project."""
    return get_db().execute(
        """
        SELECT *
        FROM sprints
        WHERE project_id = ?
        ORDER BY id DESC
        """,
        (project_id,),
    ).fetchall()


def list_sprints_with_progress(project_id):
    """
    Return all sprints for a project with simple task progress counts.

    This is okay for Sprint 2 because Sprint 2 includes showing
    simple sprint progress: total tasks, To Do, In Progress, Done,
    and percent complete.
    """
    return get_db().execute(
        """
        SELECT
            sprints.*,
            COUNT(tasks.id) AS task_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'To Do' THEN 1 ELSE 0 END), 0)
                AS to_do_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'In Progress' THEN 1 ELSE 0 END), 0)
                AS in_progress_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'Done' THEN 1 ELSE 0 END), 0)
                AS done_count
        FROM sprints
        LEFT JOIN tasks ON tasks.sprint_id = sprints.id
        WHERE sprints.project_id = ?
        GROUP BY sprints.id
        ORDER BY sprints.id DESC
        """,
        (project_id,),
    ).fetchall()


def get_sprint(sprint_id):
    """Return one sprint by id."""
    return get_db().execute(
        """
        SELECT *
        FROM sprints
        WHERE id = ?
        """,
        (sprint_id,),
    ).fetchone()


def get_sprint_with_progress(sprint_id):
    """
    Return one sprint with simple task progress counts.
    """
    return get_db().execute(
        """
        SELECT
            sprints.*,
            COUNT(tasks.id) AS task_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'To Do' THEN 1 ELSE 0 END), 0)
                AS to_do_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'In Progress' THEN 1 ELSE 0 END), 0)
                AS in_progress_count,
            COALESCE(SUM(CASE WHEN tasks.status = 'Done' THEN 1 ELSE 0 END), 0)
                AS done_count
        FROM sprints
        LEFT JOIN tasks ON tasks.sprint_id = sprints.id
        WHERE sprints.id = ?
        GROUP BY sprints.id
        """,
        (sprint_id,),
    ).fetchone()


def create_sprint(project_id, name, goal, start_date, end_date):
    """Create a new sprint inside a project."""
    timestamp = _now()

    cursor = get_db().execute(
        """
        INSERT INTO sprints
            (project_id, name, goal, start_date, end_date, status, completed_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'Active', NULL, ?, ?)
        """,
        (project_id, name, goal, start_date, end_date, timestamp, timestamp),
    )

    get_db().commit()
    return cursor.lastrowid


def update_sprint(sprint_id, name, goal, start_date, end_date):
    """Update an existing sprint."""
    get_db().execute(
        """
        UPDATE sprints
        SET name = ?,
            goal = ?,
            start_date = ?,
            end_date = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (name, goal, start_date, end_date, _now(), sprint_id),
    )

    get_db().commit()


def update_sprint_status(sprint_id, status):
    """
    Mark a sprint as Active or Completed.

    Completed sprints get a completed_at timestamp.
    Reopened sprints clear completed_at.
    """
    completed_at = _now() if status == "Completed" else None

    get_db().execute(
        """
        UPDATE sprints
        SET status = ?,
            completed_at = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (status, completed_at, _now(), sprint_id),
    )

    get_db().commit()


def delete_sprint(sprint_id):
    """Delete a sprint."""
    get_db().execute(
        """
        DELETE FROM sprints
        WHERE id = ?
        """,
        (sprint_id,),
    )

    get_db().commit()
    