from app import models
from app.db import get_db, migrate_db


def test_app_starts_successfully(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"TaskFlask" in response.data


def test_shared_javascript_asset_is_available(client):
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert b"data-task-board" in response.data


def test_database_commands_are_registered_and_migration_runs(app):
    assert {"init-db", "migrate-db"}.issubset(app.cli.commands)

    result = app.test_cli_runner().invoke(args=["migrate-db"])

    assert result.exit_code == 0
    assert "Migrated the TaskFlask database." in result.output


def test_migration_allows_any_positive_story_point_value(app, make_sprint):
    sprint_id = make_sprint()

    with app.app_context():
        db = get_db()
        db.executescript(
            """
            DROP TABLE tasks;
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sprint_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'To Do',
                priority TEXT NOT NULL DEFAULT 'Medium',
                story_points INTEGER NOT NULL DEFAULT 1
                    CHECK (story_points IN (1, 2, 3, 5, 8, 13)),
                assignee TEXT,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (sprint_id) REFERENCES sprints (id) ON DELETE CASCADE
            );
            """
        )
        db.execute(
            """
            INSERT INTO tasks (
                sprint_id, title, status, priority, story_points,
                created_at, updated_at
            )
            VALUES (?, 'Existing task', 'To Do', 'Medium', 13, ?, ?)
            """,
            (sprint_id, "2026-07-15T00:00:00+00:00", "2026-07-15T00:00:00+00:00"),
        )
        db.commit()

        migrate_db()

        db.execute(
            "UPDATE tasks SET story_points = 20 WHERE title = 'Existing task'"
        )
        db.commit()
        task = db.execute(
            """
            SELECT story_points, added_on, board_order
            FROM tasks
            WHERE title = 'Existing task'
            """
        ).fetchone()

    assert task["story_points"] == 20
    assert task["added_on"] == "2026-07-15"
    assert task["board_order"] == 0


def test_design_system_reference_page(client):
    response = client.get("/design-system")

    assert response.status_code == 200
    assert b"Design system" in response.data
    assert b"Primary action" in response.data


def test_database_initializes_successfully(app):
    with app.app_context():
        rows = get_db().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row["name"] for row in rows}
    assert {"projects", "sprints", "tasks", "activity_log"}.issubset(table_names)


def test_creating_a_project(client):
    response = client.post(
        "/projects/new",
        data={
            "name": "Capstone Planner",
            "description": "Keep our work visible.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Project created." in response.data
    assert b"Capstone Planner" in response.data


def test_project_detail_has_back_navigation(client, make_project):
    project_id = make_project()

    response = client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    assert b"Back to Projects" in response.data
    assert b'aria-label="Current project shortcuts"' in response.data
    assert b'href="#planning-cycles"' in response.data
    assert b'href="#project-burnup"' in response.data


def test_editing_a_project(client, make_project):
    project_id = make_project()

    response = client.post(
        f"/projects/{project_id}/edit",
        data={
            "name": "Updated Planner",
            "description": "A clearer project description.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Project updated." in response.data
    assert b"Updated Planner" in response.data


def test_deleting_a_project(client, make_project):
    project_id = make_project(name="Temporary Project")

    response = client.post(
        f"/projects/{project_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"deleted" in response.data
    assert b"No projects yet" in response.data


def test_dashboard_and_project_list_show_project_progress(client, make_project, make_sprint, make_task):
    project_id = make_project(name="Progress Project")
    sprint_id = make_sprint(project_id=project_id)
    make_task(sprint_id=sprint_id, title="Completed", status="Done", story_points=3)
    make_task(sprint_id=sprint_id, title="Open", status="To Do", story_points=5)

    dashboard_response = client.get("/")
    projects_response = client.get("/projects")
    detail_response = client.get(f"/projects/{project_id}")

    for response in (dashboard_response, projects_response, detail_response):
        assert response.status_code == 200
        assert b"38%" in response.data
        assert b"3 of 8 story points" in response.data


def test_project_list_expands_task_previews_with_sprint_tags(
    client, make_project, make_sprint, make_task
):
    project_id = make_project(name="Preview Tasks Project")
    first_sprint = make_sprint(project_id=project_id, name="Design Sprint")
    second_sprint = make_sprint(project_id=project_id, name="Build Sprint")
    make_task(
        sprint_id=first_sprint,
        title="Review wireframes",
        status="In Progress",
        story_points=5,
    )
    make_task(
        sprint_id=second_sprint,
        title="Create endpoint",
        status="To Do",
        story_points=8,
    )

    response = client.get("/projects")

    assert response.status_code == 200
    assert b"View tasks" in response.data
    assert b"Review wireframes" in response.data
    assert b"Design Sprint" in response.data
    assert b"Create endpoint" in response.data
    assert b"Build Sprint" in response.data
    assert b"5 SP" in response.data
    assert b"8 SP" in response.data


def test_dashboard_project_sorting(client, make_project):
    make_project(name="Zulu Project")
    make_project(name="Alpha Project")

    response = client.get("/?sort=name")

    assert response.status_code == 200
    assert response.data.index(b"Alpha Project") < response.data.index(b"Zulu Project")
    assert b'<option value="name" selected>' in response.data


def test_dashboard_uses_project_updated_timestamp(client, make_project):
    make_project(name="Timestamped Project")

    response = client.get("/")

    assert response.status_code == 200
    assert b"Updated just now" not in response.data
    assert b"Updated " in response.data


def test_dashboard_counts_distinct_task_assignees(app, make_sprint, make_task):
    sprint_id = make_sprint()
    make_task(sprint_id=sprint_id, title="Alex one", assignee="Alex")
    make_task(sprint_id=sprint_id, title="Alex two", assignee="Alex")
    make_task(sprint_id=sprint_id, title="Jordan task", assignee="Jordan")
    make_task(sprint_id=sprint_id, title="Unassigned task", assignee="")

    with app.app_context():
        summary = models.get_dashboard_counts()

    assert summary["team_member_count"] == 2


def test_dashboard_rejects_unknown_project_sort(client, make_project):
    make_project()

    response = client.get("/?sort=not-a-real-sort")

    assert response.status_code == 200
    assert b'<option value="recent" selected>' in response.data


def test_dashboard_limits_project_preview_and_links_to_full_list(client, make_project):
    for index in range(4):
        make_project(name=f"Preview Project {index}")

    response = client.get("/")

    assert response.status_code == 200
    assert response.data.count(b'class="dashboard-project-card"') == 3
    assert b"Showing 3 of 4 projects" in response.data
    assert b"View all 4 projects" in response.data


def test_dashboard_hides_view_all_when_every_project_is_visible(client, make_project):
    make_project(name="First Project")
    make_project(name="Second Project")

    response = client.get("/")

    assert response.status_code == 200
    assert b"View all" not in response.data
