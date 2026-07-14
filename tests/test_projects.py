from app import models
from app.db import get_db


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
    make_task(sprint_id=sprint_id, title="Completed", status="Done")
    make_task(sprint_id=sprint_id, title="Open", status="To Do")

    dashboard_response = client.get("/")
    projects_response = client.get("/projects")
    detail_response = client.get(f"/projects/{project_id}")

    for response in (dashboard_response, projects_response, detail_response):
        assert response.status_code == 200
        assert b"50%" in response.data
        assert b"1 of 2 tasks done" in response.data


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
