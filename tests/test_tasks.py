from app import models
from app.db import get_db


def test_task_board_supports_drag_and_drop(client, app, make_task):
    task_id = make_task(title="Drag me", status="To Do")

    with app.app_context():
        task = get_db().execute(
            "SELECT sprint_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

    response = client.get(f"/sprints/{task['sprint_id']}")

    assert response.status_code == 200
    assert b'data-task-board' in response.data
    assert b'draggable="true"' in response.data
    assert b'data-status="To Do"' in response.data
    assert b'data-status="In Progress"' in response.data
    assert b'data-status="Done"' in response.data

    script = client.get("/static/app.js")
    assert b"task-drag-preview" in script.data
    assert b"setDragImage" in script.data
    assert b'[data-drop-zone].is-drag-over' in script.data
    assert b"task-drop-indicator" in script.data
    assert b"findInsertionTarget" in script.data
    assert b'formData.append("ordered_task_ids"' in script.data


def test_task_cards_rely_on_drag_without_a_move_form(client, app, make_task):
    task_id = make_task(title="Drag only", status="To Do")

    with app.app_context():
        task = get_db().execute(
            "SELECT sprint_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

    response = client.get(f"/sprints/{task['sprint_id']}")

    assert response.status_code == 200
    assert b'class="task-card-footer"' in response.data
    assert b'aria-label="Task actions"' in response.data
    assert b'class="status-form"' not in response.data


def test_drag_order_persists_within_and_between_columns(
    client, app, make_sprint, make_task
):
    sprint_id = make_sprint()
    first_id = make_task(sprint_id=sprint_id, title="efeffe", status="Done")
    second_id = make_task(sprint_id=sprint_id, title="hbguh", status="Done")
    incoming_id = make_task(sprint_id=sprint_id, title="Incoming", status="To Do")

    same_column_response = client.post(
        f"/tasks/{second_id}/status",
        data={
            "status": "Done",
            "ordered_task_ids": [str(second_id), str(first_id)],
        },
        follow_redirects=True,
    )
    assert same_column_response.status_code == 200

    with app.app_context():
        done_titles = [
            task["title"]
            for task in models.list_tasks(sprint_id, {"status": "Done"})
        ]
    assert done_titles == ["hbguh", "efeffe"]

    cross_column_response = client.post(
        f"/tasks/{incoming_id}/status",
        data={
            "status": "Done",
            "ordered_task_ids": [
                str(second_id),
                str(incoming_id),
                str(first_id),
            ],
        },
        follow_redirects=True,
    )
    assert cross_column_response.status_code == 200

    with app.app_context():
        done_tasks = models.list_tasks(sprint_id, {"status": "Done"})

    assert [task["title"] for task in done_tasks] == ["hbguh", "Incoming", "efeffe"]
    assert [task["board_order"] for task in done_tasks] == [0, 1, 2]


def test_task_crud_and_status_flow(client, app, make_sprint):
    sprint_id = make_sprint()

    create_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={
            "title": "Original task",
            "description": "Original description",
            "status": "To Do",
            "priority": "High",
            "story_points": "5",
            "assignee": "Alex",
            "added_on": "2026-07-10",
            "due_date": "2026-07-20",
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert b"Original task" in create_response.data

    with app.app_context():
        task = get_db().execute(
            "SELECT id FROM tasks WHERE title = ?", ("Original task",)
        ).fetchone()
        task_id = task["id"]

    edit_response = client.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "Updated task",
            "description": "Updated description",
            "status": "In Progress",
            "priority": "Medium",
            "story_points": "8",
            "assignee": "Jordan",
            "added_on": "2026-07-11",
            "due_date": "2026-07-21",
        },
        follow_redirects=True,
    )
    assert b"Updated task" in edit_response.data
    assert b"Jordan" in edit_response.data
    assert b"Added 2026-07-11" in edit_response.data

    status_response = client.post(
        f"/tasks/{task_id}/status",
        data={"status": "Done"},
        follow_redirects=True,
    )
    assert b"Task status updated." in status_response.data

    filtered_response = client.get(
        f"/sprints/{sprint_id}?assignee=Jordan&priority=Medium&status=Done"
    )
    assert b"Updated task" in filtered_response.data
    assert b"Filters active" in filtered_response.data

    delete_response = client.post(
        f"/tasks/{task_id}/delete", follow_redirects=True
    )
    assert b"Task deleted." in delete_response.data
    assert b"Updated task" not in delete_response.data


def test_story_points_are_required_positive_whole_numbers(
    client, app, make_sprint
):
    sprint_id = make_sprint()
    task_data = {
        "title": "Estimate me",
        "description": "Story point validation",
        "status": "To Do",
        "priority": "Medium",
        "assignee": "",
        "due_date": "",
    }

    missing_response = client.post(
        f"/sprints/{sprint_id}/tasks/new", data=task_data
    )
    assert b"Story points are required and must be a whole number." in missing_response.data

    invalid_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={**task_data, "story_points": "2.5"},
    )
    assert b"Story points are required and must be a whole number." in invalid_response.data

    zero_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={**task_data, "story_points": "0"},
    )
    assert b"Story points must be at least 1." in zero_response.data

    invalid_date_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={**task_data, "story_points": "5", "added_on": "not-a-date"},
    )
    assert b"Added on date must use YYYY-MM-DD." in invalid_date_response.data

    valid_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={**task_data, "story_points": "20"},
        follow_redirects=True,
    )
    assert valid_response.status_code == 200
    assert b"20 SP" in valid_response.data

    with app.app_context():
        task = get_db().execute(
            "SELECT story_points FROM tasks WHERE title = ?", ("Estimate me",)
        ).fetchone()

    assert task["story_points"] == 20


def test_done_task_completed_date_can_be_created_and_edited(
    client, app, make_sprint
):
    sprint_id = make_sprint()
    task_data = {
        "title": "Historical task",
        "description": "Completed before the demo.",
        "status": "Done",
        "priority": "High",
        "story_points": "8",
        "assignee": "Alex",
        "added_on": "2026-07-10",
        "due_date": "2026-07-20",
    }

    create_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={**task_data, "completed_at": "2026-07-12"},
        follow_redirects=True,
    )

    assert create_response.status_code == 200
    assert b"Completed 2026-07-12" in create_response.data

    with app.app_context():
        task = get_db().execute(
            "SELECT id, completed_at FROM tasks WHERE title = ?",
            ("Historical task",),
        ).fetchone()
        task_id = task["id"]
        assert task["completed_at"].startswith("2026-07-12T")

    edit_page = client.get(f"/tasks/{task_id}/edit")
    assert b'name="completed_at"' in edit_page.data
    assert b'value="2026-07-12"' in edit_page.data

    edit_response = client.post(
        f"/tasks/{task_id}/edit",
        data={**task_data, "completed_at": "2026-07-14"},
        follow_redirects=True,
    )

    assert edit_response.status_code == 200
    assert b"Completed 2026-07-14" in edit_response.data

    with app.app_context():
        completed_at = get_db().execute(
            "SELECT completed_at FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()["completed_at"]

    assert completed_at.startswith("2026-07-14T")


def test_completed_date_validation_and_reopening_semantics(
    client, app, make_task
):
    task_id = make_task(
        title="Completion rules",
        status="Done",
        added_on="2026-07-10",
        completed_at="2026-07-12",
    )

    invalid_response = client.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "Completion rules",
            "description": "Date validation",
            "status": "Done",
            "priority": "Medium",
            "story_points": "1",
            "assignee": "",
            "added_on": "2026-07-10",
            "due_date": "",
            "completed_at": "2026-07-09",
        },
    )

    assert b"Completed on date cannot be before the added on date." in invalid_response.data

    reopen_response = client.post(
        f"/tasks/{task_id}/edit",
        data={
            "title": "Completion rules",
            "description": "Date validation",
            "status": "In Progress",
            "priority": "Medium",
            "story_points": "1",
            "assignee": "",
            "added_on": "2026-07-10",
            "due_date": "",
            "completed_at": "2026-07-12",
        },
        follow_redirects=True,
    )

    assert reopen_response.status_code == 200
    with app.app_context():
        completed_at = get_db().execute(
            "SELECT completed_at FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()["completed_at"]

    assert completed_at is None
