from datetime import date

VALID_SPRINT_STATUSES = ["Active", "Completed"]

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
    