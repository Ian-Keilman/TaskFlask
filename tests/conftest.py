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
    