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
