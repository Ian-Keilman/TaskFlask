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


def test_task_crud_and_status_flow(client, app, make_sprint):
    sprint_id = make_sprint()

    create_response = client.post(
        f"/sprints/{sprint_id}/tasks/new",
        data={
            "title": "Original task",
            "description": "Original description",
            "status": "To Do",
            "priority": "High",
            "assignee": "Alex",
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
            "assignee": "Jordan",
            "due_date": "2026-07-21",
        },
        follow_redirects=True,
    )
    assert b"Updated task" in edit_response.data
    assert b"Jordan" in edit_response.data

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
