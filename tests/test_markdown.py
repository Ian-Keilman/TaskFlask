from app.markdown import render_markdown


def test_markdown_renders_common_task_description_formatting():
    rendered = str(
        render_markdown(
            "## Acceptance criteria\n"
            "- [x] **Saved** to SQLite\n"
            "- [ ] Add a [test](https://example.com)\n\n"
            "Use `pytest -q`."
        )
    )

    assert "<h4>Acceptance criteria</h4>" in rendered
    assert '<input type="checkbox" disabled checked' in rendered
    assert "<strong>Saved</strong>" in rendered
    assert '<a href="https://example.com"' in rendered
    assert "<code>pytest -q</code>" in rendered


def test_markdown_escapes_html_and_rejects_unsafe_links():
    rendered = str(
        render_markdown(
            '<script>alert("x")</script> [bad](javascript:alert(1))'
        )
    )

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert 'href="javascript:' not in rendered


def test_task_board_renders_description_markdown(client, make_task, app):
    task_id = make_task(
        title="Markdown task",
        description="**Important**\n\n- first\n- second",
    )

    with app.app_context():
        from app.db import get_db

        task = get_db().execute(
            "SELECT sprint_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

    response = client.get(f"/sprints/{task['sprint_id']}")

    assert b"<strong>Important</strong>" in response.data
    assert b"<ul><li>first</li><li>second</li></ul>" in response.data


def test_project_pages_render_project_description_markdown(
    client, make_project
):
    project_id = make_project(
        name="Markdown project",
        description="**Project context**\n\n- first goal\n- second goal",
    )

    detail_response = client.get(f"/projects/{project_id}")
    list_response = client.get("/projects")
    dashboard_response = client.get("/")

    for response in (detail_response, list_response, dashboard_response):
        assert b"<strong>Project context</strong>" in response.data
        assert b"<ul><li>first goal</li><li>second goal</li></ul>" in response.data


def test_project_and_sprint_pages_render_sprint_goal_markdown(
    client, make_project, make_sprint
):
    project_id = make_project(name="Markdown project")
    sprint_id = make_sprint(
        project_id=project_id,
        name="Markdown sprint",
        goal="## Sprint goal\n- [x] Agree on scope\n- [ ] Ship it",
    )

    project_response = client.get(f"/projects/{project_id}")
    sprint_response = client.get(f"/sprints/{sprint_id}")

    for response in (project_response, sprint_response):
        assert b"<h4>Sprint goal</h4>" in response.data
        assert b'<input type="checkbox" disabled checked' in response.data
        assert b'<input type="checkbox" disabled aria-hidden="true">' in response.data
