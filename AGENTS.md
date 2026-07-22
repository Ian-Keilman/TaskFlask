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
  added-on date, due date, editable completion date, and persistent board order.
- Required positive whole-number story-point estimates.
- A sprint board with three columns: `To Do`, `In Progress`, and `Done`.
- Vanilla-JavaScript drag-and-drop task movement between board columns.
- Task filtering by assignee, priority, and status.
- Sprint and project progress calculated from completed story points over total
  story points.
- One cumulative project burnup chart that unifies story-point scope and
  completion activity across every sprint in the project.
- Safe Markdown rendering in project descriptions, sprint goals, and task
  descriptions. Raw HTML is escaped.
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
- Story-point progress helpers: [`app/progress.py`](app/progress.py).
- Cumulative project burnup-series calculations: [`app/burnup.py`](app/burnup.py).
- Safe user-authored Markdown rendering: [`app/markdown.py`](app/markdown.py).
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
- Project burnup history is reconstructed from every sprint task's `added_on`,
  `created_at`, `completed_at`, and fallback timestamps. It is cumulative, but
  it is not a complete immutable event history.
- The app is intended for local or classroom-scale use. Production deployment,
  multi-team tenancy, and external integrations are outside the current scope.

## Architecture and responsibilities

- `routes.py` handles HTTP workflow: load resources, validate requests, call the
  model layer, flash messages, redirect, and build template context.
- `forms.py` owns normalization, allowed values, and field-level validation.
- `models.py` owns all application SQL and database persistence.
- `progress.py` owns pure story-point progress calculations while preserving
  task-status counts for board summaries.
- `burnup.py` owns the pure, cumulative project-wide story-point time series.
- `markdown.py` owns the allowlisted Markdown-to-safe-HTML transformation.
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
- Task status, sprint status, and priority choices originate from constants in
  `app/forms.py`. Keep story-point validation, schema constraints, templates,
  migrations, and tests synchronized.
- Preserve `tasks.board_order` whenever tasks are created, edited, moved, or
  reordered so a board reload does not discard the user's chosen card order.
- Validation belongs in `forms.py`, following the existing `validate_*` and
  `clean_*` patterns.
- Fetch missing project, sprint, and task records through the shared
  `_require_*` route helpers so missing resources consistently return HTTP 404.
- Store timestamps in UTC. Convert only for display or Pacific calendar-day
  calculations.
- Use Post/Redirect/Get after successful create, update, delete, and lifecycle
  operations.
- Preserve `completed_at` semantics: set it when a task or sprint becomes
  completed, allow an explicit historical date for Done tasks, retain it while
  the item remains completed, and clear it when reopened.
- Reuse the shared CSS design tokens and components before adding page-specific
  styles. Check `/design-system` when changing the visual language.
- Maintain accessible labels, focus states, live regions, and confirmation text.
  Task-card actions must remain visible on touch devices and reveal on keyboard
  focus as well as pointer hover.

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
- Keep the project burnup global and cumulative across all of its sprints. Do
  not replace it with a per-sprint selector. Clear the SVG before every render,
  and hide the chart/legend for an empty series.
- Progress percentages must use completed story points divided by total story
  points. Task counts may still be displayed as board metadata, but must not
  drive progress bars.
- Task descriptions must pass through the registered `markdown` Jinja filter;
  never mark user-provided HTML safe directly.
- Keep changes narrowly scoped and preserve unrelated work in a dirty worktree.
- Add or update tests for behavior changes and run `python -m pytest -q` before
  considering the work complete.
- Keep the application runnable after every change.