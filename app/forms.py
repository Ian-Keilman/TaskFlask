def _text(form_data, field_name):
    return (form_data.get(field_name) or "").strip()


def validate_project(form_data):
    data = {
        "name": _text(form_data, "name"),
        "description": _text(form_data, "description"),
    }
    errors = {}

    if not data["name"]:
        errors["name"] = "Project name is required."

    return data, errors
