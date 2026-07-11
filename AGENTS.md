# AGENTS.md — TaskFlask

Orientation for coding agents (and humans) working in this repo. Read this
before making changes. The full build plan lives in [PLAN.md](PLAN.md).

## What this app is supposed to be

**TaskFlask** is a minimal Scrum board for small student software-engineering
teams. The intended product:

- **Users** sign up and log in with a local username + password (hashed in the
  backend, **no OAuth**).
- **Sprints** are the high-level unit of work (like an Epic). Tasks live inside a
  sprint and are tagged to it.
- **Tasks** carry: title, description, status, priority, assignee, and due date.
  Full CRUD.
- The board shows tasks as cards in **three vertical columns — To Do, In
  Progress, Done** — with **drag-and-drop** to change status.
- Tasks can be **filtered** by assignee, priority, or status.

Stack: **Flask** app-factory + Jinja server-rendered templates + **SQLite** +
**vanilla JS** for drag-and-drop. No SPA, no build step, no OAuth.

## What is actually in the repo right now

Working:
- App factory & blueprint wiring ([`app/__init__.py`](app/__init__.py)),
  request-scoped SQLite with FK enforcement ([`app/db.py`](app/db.py)).
- **Project** and **Sprint** CRUD — routes ([`app/routes.py`](app/routes.py)),
  SQL ([`app/models.py`](app/models.py)), validation
  ([`app/forms.py`](app/forms.py)), templates, and a dashboard.
- pytest suite over sprint flows ([`tests/`](tests)).

Not yet built / broken (see PLAN.md §2 for detail):
- **No users, no auth, no tasks, no board, no drag-and-drop, no filtering** —
  i.e. the actual Scrum-board feature set. `schema.sql` has only `projects` and
  `sprints`.
- `app/services.py` is **unused and would fail to import** (`from .forms import
  VALID_STATUSES`, which does not exist).
- `models.get_sprint_progress()` is a **stub returning zeros**; sprint/dashboard
  progress bars never populate.
- **1 failing test** — flash-message wording mismatch in the sprint-status route.
- `base.html` loads `static/app.js`, which **does not exist** (this is where the
  board's drag-and-drop JS should go).
- README documents a `flask migrate-db` command that is **not registered**.

## Conventions

- **All SQL is parametrized** and lives only in the SQL/repository module — never
  build queries with f-strings or `.format`.
- Keep the three status strings (`To Do`, `In Progress`, `Done`) in **one Python
  constant** and reference it everywhere (DB `CHECK`, validation, templates, JS).
- Validation goes in `forms.py`, following the existing `validate_*` pattern.
- Hash passwords with `werkzeug.security`; store only the hash. Never log secrets.
- Read `SECRET_KEY` from the environment; the `"dev"` default is local-only.

## Run & test

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app run init-db    # create/reset local SQLite DB
python run.py                        # http://127.0.0.1:5000
python -m pytest -q                  # test suite
```

## Guardrails for agents

- Do **not** add OAuth, external auth providers, or a frontend framework — the
  product is intentionally minimal.
- When you touch a status value, update the single shared constant, not one
  call site.
- Keep the app runnable after every change; prefer the milestone order in
  PLAN.md §9 (fix broken tests/dead code first).
- Get `pytest` green before adding features on top.
