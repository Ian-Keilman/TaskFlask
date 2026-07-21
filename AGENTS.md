# AGENTS.md — TaskFlask

Orientation for coding agents and humans working in this repository. Read this
before making changes.

## What TaskFlask is

**TaskFlask** is a lightweight Scrum project tracker for small student
software-engineering teams.

The current hierarchy is:

```text
Project
└── Sprint
    └── Task
```

The application currently supports:

- Full CRUD for projects, sprints, and tasks.
- Task fields for title, description, status, priority, assignee, story points,
  added-on date, and due date.
- Required Fibonacci story-point estimates: `1, 2, 3, 5, 8, 13, 21, 34, 55,
  89`.
- A sprint board with three columns: `To Do`, `In Progress`, and `Done`.
- Vanilla-JavaScript drag-and-drop task movement, with a normal HTML status form
  retained as a non-JavaScript fallback.
- Task filtering by assignee, priority, and status.
- Sprint and project progress calculated from real task data.
- Project-level sprint burnup charts comparing completed story points with total
  scope over time.
- Dashboard project sorting, live summary counts, and a three-project preview.
- Expandable task previews on the Projects page, tagged with their sprint.
- Friendly Pacific-time timestamp display and responsive, shared UI styling.

Stack: **Flask app factory**, **Jinja server-rendered templates**, **SQLite**,
shared CSS, and **vanilla JavaScript**. There is no SPA, frontend build step,
OAuth integration, or external service dependency.

## Current repository state

### Working

- Application factory, blueprint registration, Jinja filters, and configuration:
  [`app/__init__.py`](app/__init__.py).
- Request-scoped SQLite connections, foreign-key enforcement, schema
  initialization, and non-destructive migration commands:
  [`app/db.py`](app/db.py).
- Canonical clean-install schema for projects, sprints, tasks, story points, and
  timestamps: [`schema.sql`](schema.sql).
- Input normalization and validation: [`app/forms.py`](app/forms.py).
- Parameterized SQL CRUD and aggregate queries: [`app/models.py`](app/models.py).
- Task-count progress helpers: [`app/progress.py`](app/progress.py).
- Story-point burnup-series calculations: [`app/burnup.py`](app/burnup.py).
- Dashboard, project, sprint, task, filter, and status-change routes:
  [`app/routes.py`](app/routes.py).
- Server-rendered pages and helpful empty states:
  [`app/templates/`](app/templates).
- Shared design tokens, components, responsive layouts, sprint board, and burnup
  styling: [`app/static/style.css`](app/static/style.css).
- Confirmation prompts, task drag-and-drop, and burnup-chart rendering:
  [`app/static/app.js`](app/static/app.js).
- Automated tests for application setup, migrations, CRUD, navigation,
  validation, progress, task-board behavior, previews, and burnup calculations:
  [`tests/`](tests).

### Intentional limitations / unfinished areas

- There are currently **no user accounts, authentication, roles, or team
  permissions**. Do not assume that an assignee is a registered user; it is
  stored as task text.
- The `activity_log` table exists in the schema, but no current route or model
  writes activity records. Do not present it as a finished recent-activity
  feature.
- Burnup history is reconstructed from task `added_on`, `created_at`,
  `completed_at`, and fallback timestamps. It is not a complete immutable event
  history.
- The app is intended for local or classroom-scale use. Production deployment,
  multi-team tenancy, and external integrations are outside the current scope.

## Architecture and responsibilities

- `routes.py` handles HTTP workflow: load resources, validate requests, call the
  model layer, flash messages, redirect, and build template context.
- `forms.py` owns normalization, allowed values, and field-level validation.
- `models.py` owns all application SQL and database persistence.
- `progress.py` owns pure task-count progress calculations.
- `burnup.py` owns pure story-point time-series calculations.
- `templates/` owns page structure and conditional/empty-state rendering.
- `style.css` owns the design system and responsive presentation.
- `app.js` adds progressive enhancement; core CRUD must continue to work without
  JavaScript wherever a server-rendered fallback exists.

Keep these boundaries intact. In particular, do not place SQL in routes or
templates, and do not duplicate validation inside JavaScript as the only source
of truth.

## Conventions

- **Parameterize every SQL value.** Never interpolate request data into SQL with
  f-strings, `.format()`, or string concatenation.
- Task status, sprint status, priority, and story-point choices originate from
  the constants in `app/forms.py`. Keep schema constraints, templates,
  JavaScript behavior, migrations, and tests synchronized with those constants.
- Validation belongs in `forms.py`, following the existing `validate_*` and
  `clean_*` patterns.
- Fetch missing project, sprint, and task records through the shared
  `_require_*` route helpers so missing resources consistently return HTTP 404.
- Store timestamps in UTC. Convert only for display or Pacific calendar-day
  calculations.
- Use Post/Redirect/Get after successful create, update, delete, and lifecycle
  operations.
- Preserve `completed_at` semantics: set it when a task or sprint becomes
  completed, retain it while it remains completed, and clear it when reopened.
- Reuse the shared CSS design tokens and components before adding page-specific
  styles. Check `/design-system` when changing the visual language.
- Maintain accessible labels, focus states, live regions, confirmation text,
  and non-drag task-status controls.

## Database changes

For every stored-field or constraint change:

1. Update `schema.sql` for new installations.
2. Add or update a non-destructive migration in `app/db.py` for existing data.
3. Update `app/models.py` reads and writes.
4. Update validation, templates, and tests that depend on the field.

Use `init-db` only when resetting/creating a local database. Use `migrate-db`
when preserving data in an existing database.

## Run and test

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Create/reset the local SQLite database.
python -m flask --app run init-db

# Apply registered non-destructive migrations to an existing database.
python -m flask --app run migrate-db

# Run the development server at http://127.0.0.1:5000.
python run.py

# Run the complete test suite.
python -m pytest -q
```

## Guardrails for agents

- Do not add OAuth, external authentication providers, a frontend framework, or
  a build pipeline unless the requested product scope explicitly changes.
- Do not reintroduce the deleted/orphaned `services.py` split. Database access
  belongs in `models.py`; pure progress logic belongs in `progress.py` or
  `burnup.py`.
- Do not hardcode dashboard counts, progress values, timestamps, or placeholder
  data in templates.
- Do not show every project on the dashboard. The dashboard intentionally limits
  its preview to `DASHBOARD_PROJECT_LIMIT`; the Projects page is the full list.
- When switching burnup sprints, clear the previous SVG before rendering the new
  selection, and hide the chart/legend for an empty series.
- Keep changes narrowly scoped and preserve unrelated work in a dirty worktree.
- Add or update tests for behavior changes and run `python -m pytest -q` before
  considering the work complete.
- Keep the application runnable after every change.
