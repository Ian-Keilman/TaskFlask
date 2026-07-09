from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import forms, models

bp = Blueprint("main", __name__)
def _require_project(project_id):
    project = models.get_project(project_id)
    if project is None:
        abort(404)
    return project


def _require_sprint(sprint_id):
    sprint = models.get_sprint(sprint_id)
    if sprint is None:
        abort(404)
    return sprint


def _flash_errors(errors):
    for message in errors.values():
        flash(message)


@bp.route("/")
def index():
    projects = models.list_projects_with_sprint_counts()
    summary = models.get_dashboard_counts()

    return render_template(
        "index.html",
        projects=projects,
        summary=summary,
    )


@bp.route("/projects")
def projects():
    projects = models.list_projects_with_sprint_counts()
    return render_template("projects.html", projects=projects)


@bp.route("/projects/new", methods=("GET", "POST"))
def new_project():
    project = None
    errors = {}

    if request.method == "POST":
        project, errors = forms.validate_project(request.form)

        if not errors:
            project_id = models.create_project(
                project["name"],
                project["description"],
            )
            flash("Project created.")
            return redirect(url_for("main.project_detail", project_id=project_id))

        _flash_errors(errors)

    return render_template(
        "project_form.html",
        title="Create Project",
        project=project,
        errors=errors,
        form_action=url_for("main.new_project"),
    )


@bp.route("/projects/<int:project_id>")
def project_detail(project_id):
    project = _require_project(project_id)
    sprints = models.list_sprints(project_id)

    return render_template(
        "project_detail.html",
        project=project,
        sprints=sprints,
    )
    
@bp.route("/projects/<int:project_id>/edit", methods=("GET", "POST"))
def edit_project(project_id):
    project = _require_project(project_id)
    errors = {}

    if request.method == "POST":
        data, errors = forms.validate_project(request.form)

        if not errors:
            models.update_project(
                project_id,
                data["name"],
                data["description"],
            )
            flash("Project updated.")
            return redirect(url_for("main.project_detail", project_id=project_id))

        project = data
        _flash_errors(errors)

    return render_template(
        "project_form.html",
        title="Edit Project",
        project=project,
        errors=errors,
        form_action=url_for("main.edit_project", project_id=project_id),
    )

@bp.post("/projects/<int:project_id>/delete")
def delete_project(project_id):
    project = _require_project(project_id)

    models.delete_project(project_id)

    flash(f"Project '{project['name']}' deleted.")
    return redirect(url_for("main.projects"))

@bp.route("/projects/<int:project_id>/sprints/new", methods=("GET", "POST"))
def new_sprint(project_id):
    project = _require_project(project_id)
    sprint = None
    errors = {}

    if request.method == "POST":
        sprint, errors = forms.validate_sprint(request.form)

        if not errors:
            sprint_id = models.create_sprint(
                project_id,
                sprint["name"],
                sprint["goal"],
                sprint["start_date"],
                sprint["end_date"],
            )
            flash("Sprint created.")
            return redirect(url_for("main.sprint_detail", sprint_id=sprint_id))

        _flash_errors(errors)

    return render_template(
        "sprint_form.html",
        title="Create Sprint",
        project=project,
        sprint=sprint,
        errors=errors,
        form_action=url_for("main.new_sprint", project_id=project_id),
    )

@bp.route("/sprints/<int:sprint_id>")
def sprint_detail(sprint_id):
    sprint = _require_sprint(sprint_id)
    project = _require_project(sprint["project_id"])
    progress = models.get_sprint_progress(sprint_id)

    return render_template(
        "sprint_detail.html",
        sprint=sprint,
        project=project,
        progress=progress,
    )
@bp.route("/sprints/<int:sprint_id>/edit", methods=("GET", "POST"))
def edit_sprint(sprint_id):
    sprint = _require_sprint(sprint_id)
    project = _require_project(sprint["project_id"])
    errors = {}

    if request.method == "POST":
        data, errors = forms.validate_sprint(request.form)

        if not errors:
            models.update_sprint(
                sprint_id,
                data["name"],
                data["goal"],
                data["start_date"],
                data["end_date"],
            )
            flash("Sprint updated.")
            return redirect(url_for("main.sprint_detail", sprint_id=sprint_id))

        sprint = data
        _flash_errors(errors)

    return render_template(
        "sprint_form.html",
        title="Edit Sprint",
        project=project,
        sprint=sprint,
        errors=errors,
        form_action=url_for("main.edit_sprint", sprint_id=sprint_id),
    )



@bp.post("/sprints/<int:sprint_id>/delete")
def delete_sprint(sprint_id):
    sprint = _require_sprint(sprint_id)
    project_id = sprint["project_id"]

    models.delete_sprint(sprint_id)

    flash(f"Sprint '{sprint['name']}' deleted.")
    return redirect(url_for("main.project_detail", project_id=project_id))
    

@bp.post("/sprints/<int:sprint_id>/status")
def change_sprint_status(sprint_id):
    sprint = _require_sprint(sprint_id)
    new_status = request.form.get("status")

    if new_status not in forms.VALID_SPRINT_STATUSES:
        flash("Invalid sprint status.")
        return redirect(url_for("main.sprint_detail", sprint_id=sprint_id))

    models.update_sprint_status(sprint_id, new_status)

    if new_status == "Completed":
        flash("Sprint marked as completed.")
    else:
        flash("Sprint reopened.")

    return redirect(url_for("main.sprint_detail", sprint_id=sprint_id))
