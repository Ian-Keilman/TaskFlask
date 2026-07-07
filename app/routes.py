from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from . import forms, models

bp = Blueprint("main", __name__)


def _require_project(project_id):
    project = models.get_project(project_id)
    if project is None:
        abort(404)
    return project


def _flash_errors(errors):
    for message in errors.values():
        flash(message)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/projects")
def projects():
    projects = models.list_projects()
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

    return render_template(
        "project_detail.html",
        project=project,
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
