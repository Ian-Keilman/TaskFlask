from datetime import date

from app import models
from app.burnup import build_burnup_series, build_project_burnup_series
from app.db import get_db


def test_burnup_calculates_total_and_completed_story_points_by_day():
    sprint = {
        "id": 1,
        "name": "Sprint 1",
        "status": "Active",
        "start_date": None,
        "end_date": "2026-07-04",
        "created_at": "2026-07-04T08:00:00+00:00",
        "completed_at": None,
    }
    tasks = [
        {
            "story_points": 5,
            "status": "Done",
            "added_on": "2026-07-01",
            "created_at": "2026-07-04T08:00:00+00:00",
            "updated_at": "2026-07-03T10:00:00+00:00",
            "completed_at": "2026-07-03T10:00:00+00:00",
        },
        {
            "story_points": 8,
            "status": "To Do",
            "added_on": "2026-07-02",
            "created_at": "2026-07-04T08:00:00+00:00",
            "updated_at": "2026-07-02T08:00:00+00:00",
        },
    ]

    burnup = build_burnup_series(sprint, tasks, today=date(2026, 7, 4))

    assert burnup["total_points"] == 13
    assert burnup["completed_points"] == 5
    assert burnup["percent_complete"] == 38
    assert [point["total"] for point in burnup["points"]] == [5, 13, 13, 13]
    assert [point["completed"] for point in burnup["points"]] == [0, 0, 5, 5]


def test_project_burnup_is_cumulative_across_sprints():
    project = {
        "id": 1,
        "name": "Unified Project",
        "created_at": "2026-07-01T08:00:00+00:00",
    }
    sprints = [
        {"id": 1, "start_date": "2026-07-01", "created_at": "2026-07-01T08:00:00+00:00"},
        {"id": 2, "start_date": "2026-07-03", "created_at": "2026-07-03T08:00:00+00:00"},
    ]
    tasks = [
        {
            "sprint_id": 1,
            "story_points": 3,
            "status": "Done",
            "added_on": "2026-07-01",
            "completed_at": "2026-07-02T12:00:00+00:00",
            "updated_at": "2026-07-02T12:00:00+00:00",
        },
        {
            "sprint_id": 2,
            "story_points": 5,
            "status": "To Do",
            "added_on": "2026-07-03",
            "updated_at": "2026-07-03T12:00:00+00:00",
        },
    ]

    burnup = build_project_burnup_series(
        project, sprints, tasks, today=date(2026, 7, 4)
    )

    assert burnup["sprint_count"] == 2
    assert burnup["total_points"] == 8
    assert burnup["completed_points"] == 3
    assert burnup["percent_complete"] == 38
    assert [point["total"] for point in burnup["points"]] == [3, 3, 8, 8]
    assert [point["completed"] for point in burnup["points"]] == [0, 3, 3, 3]


def test_project_burnup_query_combines_tasks_from_every_sprint(
    app, make_project, make_sprint, make_task
):
    project_id = make_project(name="Chart Project")
    first_sprint_id = make_sprint(
        project_id=project_id,
        name="Foundation Sprint",
        start_date="2026-07-01",
        end_date="2026-07-10",
    )
    second_sprint_id = make_sprint(
        project_id=project_id,
        name="Polish Sprint",
        start_date="2026-07-11",
        end_date="2026-07-20",
    )
    make_task(sprint_id=first_sprint_id, title="Complete", status="Done", story_points=8)
    make_task(sprint_id=second_sprint_id, title="Open", status="To Do", story_points=13)

    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE tasks SET added_on = ?, created_at = ?, updated_at = ? WHERE title = ?",
            ("2026-07-01", "2026-07-10T08:00:00+00:00", "2026-07-03T08:00:00+00:00", "Complete"),
        )
        db.execute(
            "UPDATE tasks SET added_on = ?, created_at = ?, updated_at = ? WHERE title = ?",
            ("2026-07-02", "2026-07-10T08:00:00+00:00", "2026-07-02T08:00:00+00:00", "Open"),
        )
        db.commit()
        burnup = models.get_project_burnup(project_id)

    assert burnup["name"] == "Chart Project"
    assert burnup["sprint_count"] == 2
    assert burnup["total_points"] == 21
    assert burnup["completed_points"] == 8


def test_project_page_renders_burnup_chart(client, make_project, make_sprint):
    project_id = make_project(name="Burnup Project")
    make_sprint(project_id=project_id, name="Burnup Sprint")

    response = client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    assert b"Project burnup" in response.data
    assert b"Progress tracking" in response.data
    assert b"data-burnup-chart" in response.data
    assert b"across every sprint" in response.data
    assert b"All 1 sprint" in response.data
    assert b"data-burnup-select" not in response.data
    assert response.data.index(b"Planning cycles") < response.data.index(b"Project burnup")