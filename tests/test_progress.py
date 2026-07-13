from app import models
from app.progress import calculate_progress, progress_from_counts


def test_progress_helpers_import_and_calculate_task_counts():
    tasks = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "Done"},
        {"status": "Done"},
    ]

    assert calculate_progress(tasks) == {
        "total": 4,
        "to_do": 1,
        "in_progress": 1,
        "done": 2,
        "percent_complete": 50,
    }
    assert progress_from_counts(0, 0, 0, 0)["percent_complete"] == 0


def test_sprint_progress_comes_from_database(app, make_sprint, make_task):
    sprint_id = make_sprint()
    make_task(sprint_id=sprint_id, title="Open", status="To Do")
    make_task(sprint_id=sprint_id, title="Working", status="In Progress")
    make_task(sprint_id=sprint_id, title="Complete", status="Done")

    with app.app_context():
        progress = models.get_sprint_progress(sprint_id)

    assert progress == {
        "total": 3,
        "to_do": 1,
        "in_progress": 1,
        "done": 1,
        "percent_complete": 33,
    }


def test_list_sprints_exposes_template_progress_fields(
    app, make_project, make_sprint, make_task
):
    project_id = make_project()
    sprint_id = make_sprint(project_id=project_id)
    make_task(sprint_id=sprint_id, title="Complete", status="Done")
    make_task(sprint_id=sprint_id, title="Open", status="To Do")

    with app.app_context():
        sprint = models.list_sprints(project_id)[0]

    assert sprint["total"] == 2
    assert sprint["done"] == 1
    assert sprint["percent_complete"] == 50
