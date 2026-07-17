import pytest

from app import create_app
from app.db import get_db, init_db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "taskflask-test.sqlite"

    test_app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(db_path),
            "SECRET_KEY": "test-secret",
        }
    )

    with test_app.app_context():
        init_db()

    yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_project(app, client):
    def _make_project(name="Class Project", description="A project for the team."):
        response = client.post(
            "/projects/new",
            data={
                "name": name,
                "description": description,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        with app.app_context():
            row = get_db().execute(
                """
                SELECT id
                FROM projects
                WHERE name = ?
                ORDER BY id DESC
                """,
                (name,),
            ).fetchone()

        assert row is not None
        return row["id"]

    return _make_project


@pytest.fixture
def make_sprint(app, client, make_project):
    def _make_sprint(
        project_id=None,
        name="Sprint 1",
        goal="Get the basic app working.",
        start_date="2026-06-22",
        end_date="2026-06-29",
    ):
        if project_id is None:
            project_id = make_project()

        response = client.post(
            f"/projects/{project_id}/sprints/new",
            data={
                "name": name,
                "goal": goal,
                "start_date": start_date,
                "end_date": end_date,
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        with app.app_context():
            row = get_db().execute(
                """
                SELECT id
                FROM sprints
                WHERE project_id = ? AND name = ?
                ORDER BY id DESC
                """,
                (project_id, name),
            ).fetchone()

        assert row is not None
        return row["id"]

    return _make_sprint


@pytest.fixture
def make_task(app, client, make_sprint):
    def _make_task(
        sprint_id=None,
        title="Task 1",
        description="A task for the sprint.",
        status="To Do",
        priority="Medium",
        story_points=1,
        assignee="",
        due_date="",
    ):
        if sprint_id is None:
            sprint_id = make_sprint()

        response = client.post(
            f"/sprints/{sprint_id}/tasks/new",
            data={
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "story_points": str(story_points),
                "assignee": assignee,
                "due_date": due_date,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

        with app.app_context():
            row = get_db().execute(
                """
                SELECT id FROM tasks
                WHERE sprint_id = ? AND title = ?
                ORDER BY id DESC
                """,
                (sprint_id, title),
            ).fetchone()

        assert row is not None
        return row["id"]

    return _make_task