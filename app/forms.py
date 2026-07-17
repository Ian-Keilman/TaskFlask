from datetime import date, datetime
from zoneinfo import ZoneInfo

VALID_SPRINT_STATUSES = ["Active", "Completed"]
VALID_STATUSES = ["To Do", "In Progress", "Done"]
VALID_PRIORITIES = ["Low", "Medium", "High"]
VALID_STORY_POINTS = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
PACIFIC_TIME = ZoneInfo("America/Los_Angeles")


def _text(form_data, field_name):
    return (form_data.get(field_name) or "").strip()


def _looks_like_date(value):
    if not value:
        return True

    try:
        date.fromisoformat(value)
    except ValueError:
        return False

    return True


def validate_project(form_data):
    data = {
        "name": _text(form_data, "name"),
        "description": _text(form_data, "description"),
    }
    errors = {}

    if not data["name"]:
        errors["name"] = "Project name is required."

    return data, errors


def validate_sprint(form_data):
    data = {
        "name": _text(form_data, "name"),
        "goal": _text(form_data, "goal"),
        "start_date": _text(form_data, "start_date"),
        "end_date": _text(form_data, "end_date"),
    }

    errors = {}

    if not data["name"]:
        errors["name"] = "Sprint name is required."

    if not _looks_like_date(data["start_date"]):
        errors["start_date"] = "Start date must use YYYY-MM-DD."

    if not _looks_like_date(data["end_date"]):
        errors["end_date"] = "End date must use YYYY-MM-DD."

    if data["start_date"] and data["end_date"]:
        if data["end_date"] < data["start_date"]:
            errors["end_date"] = "End date should be on or after the start date."

    return data, errors


def validate_task(form_data):
    story_points_value = _text(form_data, "story_points")

    data = {
        "title": _text(form_data, "title"),
        "description": _text(form_data, "description"),
        "status": _text(form_data, "status") or "To Do",
        "priority": _text(form_data, "priority") or "Medium",
        "story_points": None,
        "assignee": _text(form_data, "assignee"),
        "added_on": _text(form_data, "added_on")
        or datetime.now(PACIFIC_TIME).date().isoformat(),
        "due_date": _text(form_data, "due_date"),
    }

    errors = {}

    if story_points_value:
        try:
            data["story_points"] = int(story_points_value)
        except ValueError:
            pass

    if not data["title"]:
        errors["title"] = "Task title is required."

    if data["status"] not in VALID_STATUSES:
        errors["status"] = "Choose a valid status."

    if data["priority"] not in VALID_PRIORITIES:
        errors["priority"] = "Choose a valid priority."

    if data["story_points"] is None:
        errors["story_points"] = "Story points are required."
    elif data["story_points"] not in VALID_STORY_POINTS:
        errors["story_points"] = "Choose a Fibonacci estimate."

    if not _looks_like_date(data["due_date"]):
        errors["due_date"] = "Due date must use YYYY-MM-DD."

    if not _looks_like_date(data["added_on"]):
        errors["added_on"] = "Added on date must use YYYY-MM-DD."

    return data, errors


def clean_task_filters(args):
    filters = {
        "assignee": _text(args, "assignee"),
        "priority": _text(args, "priority"),
        "status": _text(args, "status"),
    }

    if filters["priority"] not in VALID_PRIORITIES:
        filters["priority"] = ""

    if filters["status"] not in VALID_STATUSES:
        filters["status"] = ""

    return filters
    