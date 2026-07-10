from datetime import datetime, timezone

from .db import get_db


def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

# Return all projects, newest updated first.
def list_projects():
    return get_db().execute(
        """
        SELECT *
        FROM projects
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()

# Return one project by id.
def get_project(project_id):
    return get_db().execute(
        """
        SELECT *
        FROM projects
        WHERE id = ?
        """,
        (project_id,),
    ).fetchone()

# Create a new project.
def create_project(name, description):
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

# Update an existing project.
def update_project(project_id, name, description):
    get_db().execute(
        """
        UPDATE projects
        SET name = ?, description = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, description, _now(), project_id),
    )

    get_db().commit()

# Delete a project
def delete_project(project_id):
    """
    Delete a project.
    """
    get_db().execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
        (project_id,),
    )

    get_db().commit()
    
#Return all sprints for one project.
def list_sprints(project_id):
    return get_db().execute(
        """
        SELECT *
        FROM sprints
        WHERE project_id = ?
        ORDER BY id DESC
        """,
        (project_id,),
    ).fetchall()

# Return one sprint by id.
def get_sprint(sprint_id):
    return get_db().execute(
        """
        SELECT *
        FROM sprints
        WHERE id = ?
        """,
        (sprint_id,),
    ).fetchone()

# Create a new sprint under a project.
def create_sprint(project_id, name, goal, start_date, end_date):
    timestamp = _now()

    cursor = get_db().execute(
        """
        INSERT INTO sprints
            (project_id, name, goal, start_date, end_date, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            name,
            goal,
            start_date,
            end_date,
            "Active",
            timestamp,
            timestamp,
        ),
    )

    get_db().commit()
    return cursor.lastrowid

# Update an existing sprint.
def update_sprint(sprint_id, name, goal, start_date, end_date):
    get_db().execute(
        """
        UPDATE sprints
        SET name = ?, goal = ?, start_date = ?, end_date = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, goal, start_date, end_date, _now(), sprint_id),
    )

    get_db().commit()

# Delete a sprint
def delete_sprint(sprint_id):
    get_db().execute(
        """
        DELETE FROM sprints
        WHERE id = ?
        """,
        (sprint_id,),
    )

    get_db().commit()

# Mark a sprint as Active or Completed.
def update_sprint_status(sprint_id, status):
    timestamp = _now()
    completed_at = timestamp if status == "Completed" else None

    get_db().execute(
        """
        UPDATE sprints
        SET status = ?, completed_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, completed_at, timestamp, sprint_id),
    )

    get_db().commit()

# Return simple sprint progress.
def get_sprint_progress(sprint_id):
    return {
        "total": 0,
        "to_do": 0,
        "in_progress": 0,
        "done": 0,
        "percent_complete": 0,
    }

def list_projects_with_sprint_counts():
    return get_db().execute(
        """
        SELECT
            projects.*,
            COALESCE(SUM(CASE WHEN sprints.status = 'Active' THEN 1 ELSE 0 END), 0) AS active_sprint_count,
            COALESCE(SUM(CASE WHEN sprints.status = 'Completed' THEN 1 ELSE 0 END), 0) AS completed_sprint_count
        FROM projects
        LEFT JOIN sprints ON sprints.project_id = projects.id
        GROUP BY projects.id
        ORDER BY projects.updated_at DESC, projects.id DESC
        """
    ).fetchall()

def get_dashboard_counts():
    return get_db().execute(
        """
        SELECT
            (SELECT COUNT(*) FROM projects) AS project_count,
            (SELECT COUNT(*) FROM sprints WHERE status = 'Active') AS active_sprint_count,
            0 AS team_member_count
        """
    ).fetchone()
