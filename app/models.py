from datetime import datetime, timezone

from .db import get_db
from .progress import progress_from_counts, with_progress


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


# Delete a project.
def delete_project(project_id):
    get_db().execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
        (project_id,),
    )

    get_db().commit()


# Return all sprints for one project.
def list_sprints(project_id):
    rows = get_db().execute(
        """
        SELECT
            sprints.*,
            COUNT(tasks.id) AS task_count,
            SUM(CASE WHEN tasks.status = 'To Do' THEN 1 ELSE 0 END) AS to_do_count,
            SUM(CASE WHEN tasks.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
            SUM(CASE WHEN tasks.status = 'Done' THEN 1 ELSE 0 END) AS done_count
        FROM sprints
        LEFT JOIN tasks ON tasks.sprint_id = sprints.id
        WHERE sprints.project_id = ?
        GROUP BY sprints.id
        ORDER BY sprints.id DESC
        """,
        (project_id,),
    ).fetchall()
    return [with_progress(row) for row in rows]


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


# Delete a sprint.
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


# Return simple sprint progress based on task statuses.
def get_sprint_progress(sprint_id):
    row = get_db().execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(CASE WHEN status = 'To Do' THEN 1 ELSE 0 END), 0) AS to_do,
            COALESCE(SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END), 0) AS in_progress,
            COALESCE(SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END), 0) AS done
        FROM tasks
        WHERE sprint_id = ?
        """,
        (sprint_id,),
    ).fetchone()

    return progress_from_counts(
        row["total"], row["to_do"], row["in_progress"], row["done"]
    )


PROJECT_SORTS = {"recent", "name", "progress"}


def list_projects_with_sprint_counts(sort="recent"):
    rows = get_db().execute(
        """
        SELECT
            projects.*,
            (SELECT COUNT(*) FROM sprints WHERE project_id = projects.id AND status = 'Active') AS active_sprint_count,
            (SELECT COUNT(*) FROM sprints WHERE project_id = projects.id AND status = 'Completed') AS completed_sprint_count,
            COUNT(tasks.id) AS task_count,
            SUM(CASE WHEN tasks.status = 'To Do' THEN 1 ELSE 0 END) AS to_do_count,
            SUM(CASE WHEN tasks.status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_count,
            SUM(CASE WHEN tasks.status = 'Done' THEN 1 ELSE 0 END) AS done_count
        FROM projects
        LEFT JOIN sprints ON sprints.project_id = projects.id
        LEFT JOIN tasks ON tasks.sprint_id = sprints.id
        GROUP BY projects.id
        ORDER BY projects.updated_at DESC, projects.id DESC
        """
    ).fetchall()
    projects = [with_progress(row) for row in rows]

    if sort == "name":
        projects.sort(key=lambda project: project["name"].casefold())
    elif sort == "progress":
        projects.sort(key=lambda project: project["percent_complete"], reverse=True)

    return projects


def get_dashboard_counts():
    return get_db().execute(
        """
        SELECT
            (SELECT COUNT(*) FROM projects) AS project_count,
            (SELECT COUNT(*) FROM sprints WHERE status = 'Active') AS active_sprint_count,
            (
                SELECT COUNT(DISTINCT assignee)
                FROM tasks
                WHERE assignee IS NOT NULL AND TRIM(assignee) != ''
            ) AS team_member_count
        """
    ).fetchone()


# -------------------------
# Sprint 3 task functions
# -------------------------

# Return all tasks for one sprint, with optional filters.
def list_tasks(sprint_id, filters=None):
    filters = filters or {}

    query = """
        SELECT *
        FROM tasks
        WHERE sprint_id = ?
    """
    params = [sprint_id]

    if filters.get("assignee"):
        query += " AND assignee = ?"
        params.append(filters["assignee"])

    if filters.get("priority"):
        query += " AND priority = ?"
        params.append(filters["priority"])

    if filters.get("status"):
        query += " AND status = ?"
        params.append(filters["status"])

    query += """
        ORDER BY
            CASE status
                WHEN 'To Do' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Done' THEN 3
                ELSE 4
            END,
            CASE priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END,
            created_at ASC
    """

    return get_db().execute(query, params).fetchall()


# Return one task by id.
def get_task(task_id):
    return get_db().execute(
        """
        SELECT *
        FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    ).fetchone()


# Create a new task inside a sprint.
def create_task(sprint_id, title, description, status, priority, assignee, due_date):
    timestamp = _now()

    cursor = get_db().execute(
        """
        INSERT INTO tasks
            (sprint_id, title, description, status, priority, assignee, due_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sprint_id,
            title,
            description,
            status,
            priority,
            assignee,
            due_date,
            timestamp,
            timestamp,
        ),
    )

    get_db().commit()
    return cursor.lastrowid


# Update an existing task.
def update_task(task_id, title, description, status, priority, assignee, due_date):
    get_db().execute(
        """
        UPDATE tasks
        SET title = ?,
            description = ?,
            status = ?,
            priority = ?,
            assignee = ?,
            due_date = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            title,
            description,
            status,
            priority,
            assignee,
            due_date,
            _now(),
            task_id,
        ),
    )

    get_db().commit()


# Move a task between To Do, In Progress, and Done.
def update_task_status(task_id, status):
    get_db().execute(
        """
        UPDATE tasks
        SET status = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, _now(), task_id),
    )

    get_db().commit()


# Delete a task.
def delete_task(task_id):
    get_db().execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    get_db().commit()


# Return assignees for the filter dropdown.
def list_assignees(sprint_id):
    rows = get_db().execute(
        """
        SELECT DISTINCT assignee
        FROM tasks
        WHERE sprint_id = ?
            AND assignee IS NOT NULL
            AND TRIM(assignee) != ''
        ORDER BY assignee
        """,
        (sprint_id,),
    ).fetchall()
    return [row["assignee"] for row in rows]