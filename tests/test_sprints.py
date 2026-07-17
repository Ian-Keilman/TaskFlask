from app.db import get_db


def test_creating_a_sprint(client, make_project):
    project_id = make_project()

    response = client.post(
        f"/projects/{project_id}/sprints/new",
        data={
            "name": "Sprint 1",
            "goal": "Build the class demo flow.",
            "start_date": "2026-06-22",
            "end_date": "2026-06-29",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Sprint created." in response.data
    assert b"Sprint 1" in response.data


def test_sprint_detail_has_back_navigation(client, make_sprint):
    sprint_id = make_sprint()

    response = client.get(f"/sprints/{sprint_id}")

    assert response.status_code == 200
    assert b"Back to Project" in response.data


def test_editing_a_sprint(client, make_sprint):
    sprint_id = make_sprint()

    response = client.post(
        f"/sprints/{sprint_id}/edit",
        data={
            "name": "Sprint 1 Revised",
            "goal": "Tighten the MVP.",
            "start_date": "2026-06-23",
            "end_date": "2026-06-30",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Sprint updated." in response.data
    assert b"Sprint 1 Revised" in response.data


def test_completing_and_reopening_a_sprint(client, app, make_sprint):
    sprint_id = make_sprint()

    complete_response = client.post(
        f"/sprints/{sprint_id}/status",
        data={"status": "Completed"},
        follow_redirects=True,
    )

    assert complete_response.status_code == 200
    assert b"Sprint marked completed." in complete_response.data
    assert b"Completed" in complete_response.data

    with app.app_context():
        sprint = get_db().execute(
            "SELECT status, completed_at FROM sprints WHERE id = ?",
            (sprint_id,),
        ).fetchone()

    assert sprint["status"] == "Completed"
    assert sprint["completed_at"] is not None

    reopen_response = client.post(
        f"/sprints/{sprint_id}/status",
        data={"status": "Active"},
        follow_redirects=True,
    )

    assert reopen_response.status_code == 200
    assert b"Sprint reopened." in reopen_response.data

    with app.app_context():
        sprint = get_db().execute(
            "SELECT status, completed_at FROM sprints WHERE id = ?",
            (sprint_id,),
        ).fetchone()

    assert sprint["status"] == "Active"
    assert sprint["completed_at"] is None


def test_deleting_a_sprint(client, make_sprint):
    sprint_id = make_sprint()

    response = client.post(
        f"/sprints/{sprint_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"deleted" in response.data.lower()


def test_sprint_name_is_required(client, make_project):
    project_id = make_project()

    response = client.post(
        f"/projects/{project_id}/sprints/new",
        data={
            "name": "",
            "goal": "Missing sprint name.",
            "start_date": "2026-06-22",
            "end_date": "2026-06-29",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Sprint name is required." in response.data


def test_sprint_end_date_cannot_be_before_start_date(client, make_project):
    project_id = make_project()

    response = client.post(
        f"/projects/{project_id}/sprints/new",
        data={
            "name": "Bad Date Sprint",
            "goal": "Test date validation.",
            "start_date": "2026-06-29",
            "end_date": "2026-06-22",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"End date should be on or after the start date." in response.data