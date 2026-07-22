from app import models
from app.progress import calculate_progress, progress_from_counts


def test_progress_helpers_import_and_calculate_task_counts():
    tasks = [
        {"status": "To Do", "story_points": 2},
        {"status": "In Progress", "story_points": 3},
        {"status": "Done", "story_points": 5},
        {"status": "Done", "story_points": 8},
    ]

    assert calculate_progress(tasks) == {
        "total": 4,
        "to_do": 1,
        "in_progress": 1,
        "done": 2,
        "total_points": 18,
        "completed_points": 13,
        "percent_complete": 72,
    }
    assert progress_from_counts(0, 0, 0, 0)["percent_complete"] == 0


def test_sprint_progress_comes_from_database(app, make_sprint, make_task):
    sprint_id = make_sprint()
    make_task(sprint_id=sprint_id, title="Open", status="To Do", story_points=2)
    make_task(sprint_id=sprint_id, title="Working", status="In Progress", story_points=3)
    make_task(sprint_id=sprint_id, title="Complete", status="Done", story_points=5)

    with app.app_context():
        progress = models.get_sprint_progress(sprint_id)

    assert progress == {
        "total": 3,
        "to_do": 1,
        "in_progress": 1,
        "done": 1,
        "total_points": 10,
        "completed_points": 5,
        "percent_complete": 50,
    }


def test_list_sprints_exposes_template_progress_fields(
    app, make_project, make_sprint, make_task
):
    project_id = make_project()
    sprint_id = make_sprint(project_id=project_id)
    make_task(sprint_id=sprint_id, title="Complete", status="Done", story_points=8)
    make_task(sprint_id=sprint_id, title="Open", status="To Do", story_points=13)

    with app.app_context():
        sprint = models.list_sprints(project_id)[0]

    assert sprint["total"] == 2
    assert sprint["done"] == 1
    assert sprint["total_points"] == 21
    assert sprint["completed_points"] == 8
    assert sprint["percent_complete"] == 38