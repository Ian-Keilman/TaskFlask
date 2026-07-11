# TaskFlask — Minimal Scrum Board: Implementation & Architecture Plan

> TA feedback + build plan for turning the current project/sprint tracker into a
> minimal Scrum board with **To Do → In Progress → Done** columns, tasks, users,
> drag-and-drop, and filtering.

---

## 1. Goal

A lightweight Scrum board where a logged-in user can:

1. Sign up / log in (local password auth, hashed — no OAuth).
2. Organize work under **Sprints** (the high-level unit, like an Epic).
3. Create **Tasks** inside a sprint, each with title, description, status, priority, assignee, and due date.
4. Do full task CRUD; every task is tagged to exactly one sprint.
5. See tasks as cards in **3 vertical columns** and **drag-and-drop** them to change status.
6. **Filter** the board by assignee, priority, or status.

Keep the stack the team already uses: **Flask + server-rendered Jinja + SQLite + vanilla JS**. No new frameworks required.

---

## 2. Scrutiny of the Current Codebase

The scaffolding (app factory, blueprint, request-scoped DB, form validation, tests) is clean and idiomatic. But the Scrum-board core does not exist yet, and several pieces are half-wired. Findings below are ordered by severity.

### 2.1 Broken / dead code

- **`app/services.py` is orphaned and would crash if imported.** It is imported by *nothing* (routes uses `models`, verified by grep). Its first line is `from .forms import VALID_STATUSES` — but [`forms.py`](app/forms.py) only defines `VALID_SPRINT_STATUSES`, so the moment anything imports `services`, it raises `ImportError`. The app only boots because `services` is never reached. The "real" progress logic (`calculate_progress`, `progress_from_counts`, `with_progress`) therefore does nothing.
- **`models.get_sprint_progress()` is a stub** ([models.py](app/models.py)) — it returns hardcoded zeros. This is the version actually used by `sprint_detail`. So the progress feature that `services.py` was meant to provide is dead on both ends.
- **`list_projects_with_sprint_counts()` doesn't return the columns the templates read.** [project_detail.html:85](app/templates/project_detail.html) reads `sprint.total`, `sprint.percent_complete`, `sprint.done`, but `list_sprints()` selects none of those. Every sprint therefore always renders "No tasks added yet." Same for the dashboard.

### 2.2 Failing / incorrect

- **1 test fails.** `test_completing_and_reopening_a_sprint` expects the flash `"Sprint marked completed."` but [routes.py:218](app/routes.py) flashes `"Sprint marked as completed."`. Either the message or the test is wrong; they must agree. (`5 passed, 1 failed`.)
- **`base.html` loads a missing script.** [base.html:8](app/templates/base.html) does `<script src=".../app.js">` but `app/static/` contains only `style.css`. Every page 404s on `app.js`. (This file is exactly where the board's drag-and-drop JS should live — see §7.)
- **README documents a command that doesn't exist.** README tells users to run `flask migrate-db`, but only `init-db` is registered ([`__init__.py`](app/__init__.py) / [`db.py`](app/db.py)). Verified: `app.cli.commands == ['init-db']`.

### 2.3 Missing for the actual product

- **No `users` table, no `tasks` table** in [schema.sql](schema.sql) — the two things the assignment is actually about. Only `projects` and `sprints` exist.
- **No authentication of any kind.** No signup/login, no session, no password hashing. `SECRET_KEY="dev"` is hardcoded in [`__init__.py`](app/__init__.py).
- **`get_dashboard_counts()` hardcodes `team_member_count = 0`** and the dashboard "Team Members" tile is permanently 0.
- **Hardcoded UI copy pretending to be data.** [index.html:96](app/templates/index.html) always prints "Updated just now" regardless of `updated_at`.

### 2.4 Naming / structure smell

- The **`models.py` vs `services.py` split is backwards from convention.** `models.py` holds raw SQL CRUD; `services.py` holds pure helpers and is unused. Recommend: rename the SQL layer to `repository.py` (or keep `models.py`), delete `services.py`, and fix the broken import if any of that logic is salvaged. Pick one module per concern and wire it in.

**Bottom line:** the project/sprint CRUD half works; the board, tasks, users, auth, progress, and drag-and-drop are all absent or stubbed. This plan fills those in.

---

## 3. Target Architecture

Server-rendered pages for navigation + a thin JSON endpoint for the drag-and-drop and filter interactions. No SPA.

```
Browser
  ├─ Jinja pages (board, auth, sprint list)          server-rendered HTML
  └─ static/app.js  ──fetch()──►  JSON task endpoints  (move / create / update)
                                        │
Flask (app factory + blueprints)        │
  ├─ auth_bp      /signup /login /logout
  ├─ board_bp     /sprints/<id>/board          (renders 3 columns)
  ├─ task_bp      /sprints/<id>/tasks  (CRUD)  + /tasks/<id>/move  (JSON)
  └─ sprint_bp    existing sprint/project routes
        │
  repository.py   parametrized SQL (one module, request-scoped sqlite3)
        │
  SQLite (schema.sql):  users · projects · sprints · tasks
```

Layering rules:

- **Routes** parse/validate input, enforce auth, call the repository, render or return JSON. No SQL in routes.
- **repository.py** is the *only* place with SQL. Always parametrized (never f-strings) — SQLite is unforgiving and injection is the #1 risk here.
- **forms.py** stays the validation layer; extend it with `validate_task` and `validate_credentials`.
- **Auth** via Flask's signed session cookie + `werkzeug.security` for hashing. No extra deps.

---

## 4. Minimal Database Schema

Add two tables and keep the existing two. `projects` stays as an optional grouping (a sprint already has `project_id`); it is not required by the assignment but is already wired, so we keep it rather than churn.

```sql
-- users: local auth only
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,          -- werkzeug generate_password_hash (pbkdf2/scrypt)
    created_at    TEXT NOT NULL
);

-- sprints: the high-level unit of work (Epic). Already exists; unchanged.

-- tasks: the board cards. Every task is tagged to exactly one sprint.
CREATE TABLE tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id    INTEGER NOT NULL,        -- "tagged by sprint"
    title        TEXT NOT NULL,
    description  TEXT,
    status       TEXT NOT NULL DEFAULT 'To Do'
                 CHECK (status IN ('To Do','In Progress','Done')),
    priority     TEXT NOT NULL DEFAULT 'Medium'
                 CHECK (priority IN ('Low','Medium','High')),
    assignee_id  INTEGER,                 -- nullable = unassigned; FK to users
    due_date     TEXT,                    -- ISO YYYY-MM-DD, nullable
    position     INTEGER NOT NULL DEFAULT 0,  -- ordering within a column
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    FOREIGN KEY (sprint_id)   REFERENCES sprints (id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users (id)   ON DELETE SET NULL
);

CREATE INDEX idx_tasks_sprint ON tasks (sprint_id);
```

Notes:
- **`status` is the column identity** — three allowed values, enforced by a `CHECK` so bad drops can't corrupt the board. Mirror these values in one Python constant (`TASK_STATUSES = ["To Do", "In Progress", "Done"]`) so DB, validation, and templates share a single source of truth.
- **`position`** lets a drop set relative order within a column. Simplest v1: reassign on move. Keep it if ordering matters; drop it if "just group by status" is enough for the demo.
- `ON DELETE SET NULL` for assignee means deleting a user leaves their tasks unassigned rather than deleting them.
- Foreign keys already enforced — [db.py](app/db.py) runs `PRAGMA foreign_keys = ON`. Good.

---

## 5. Authentication (minimal, hashed, no OAuth)

Use `werkzeug.security.generate_password_hash` / `check_password_hash` (ships with Flask) and Flask's session cookie. No new dependency.

| Route | Method | Behavior |
|---|---|---|
| `/signup` | GET/POST | Validate username unique + password length ≥ 8; store `password_hash`; log in. |
| `/login` | GET/POST | Look up user; `check_password_hash`; set `session["user_id"]`. |
| `/logout` | POST | `session.clear()`. |

- **`login_required` decorator**: redirect to `/login` if `session.get("user_id")` is missing. Apply to all board/task/sprint mutation routes.
- **`load_logged_in_user`** via `@app.before_request` → stash the user on `g.user` for templates (show username in the nav, populate assignee dropdowns).
- Move `SECRET_KEY` out of source: read from env (`os.environ`), fall back to `"dev"` only when not in production. Required — the session cookie's integrity depends on it.
- Store **only the hash**, never the plaintext. Never log passwords.

Password entry stays on the user's own device via the browser form — the app never handles third-party credentials.

---

## 6. Task Model + CRUD

Repository functions (all parametrized SQL, `updated_at` bumped on every write):

```
create_task(sprint_id, title, description, priority, assignee_id, due_date)
get_task(task_id)
list_tasks(sprint_id, *, status=None, assignee_id=None, priority=None)   # filters in SQL
update_task(task_id, **fields)          # title/description/priority/assignee/due_date
move_task(task_id, new_status, position)  # status change from drag-and-drop
delete_task(task_id)
```

Routes (`task_bp`):

| Route | Method | Purpose |
|---|---|---|
| `/sprints/<sid>/tasks/new` | GET/POST | Create form + handler |
| `/tasks/<id>/edit` | GET/POST | Edit form + handler |
| `/tasks/<id>/delete` | POST | Delete |
| `/tasks/<id>/move` | POST (JSON) | `{ "status": "In Progress", "position": 2 }` → validate status against `TASK_STATUSES`, update, return `204`/JSON |

Add `validate_task(form)` to [forms.py](app/forms.py): title required; `priority in {Low,Medium,High}`; `status in TASK_STATUSES`; `due_date` optional but must pass the existing `_looks_like_date`; `assignee_id` optional and must reference a real user. Reuse the existing validation pattern.

---

## 7. Board UI + Drag-and-Drop

**Page:** `GET /sprints/<id>/board` renders three `<section class="column" data-status="...">` elements. The route calls `list_tasks(sprint_id, **filters)`, groups rows by status in Python, and renders a `task_card.html` partial per task.

```
┌── To Do ──────┐  ┌── In Progress ─┐  ┌── Done ───────┐
│ [task card]   │  │ [task card]    │  │ [task card]   │
│ [task card]   │  │                │  │ [task card]   │
└───────────────┘  └────────────────┘  └───────────────┘
```

**Drag-and-drop: native HTML5 Drag and Drop API — zero dependencies.** This is the "minimal, nice" choice and it fixes the already-referenced-but-missing [`app/static/app.js`](app/templates/base.html):

1. Each card: `draggable="true"`, `data-task-id`. On `dragstart`, stash the id in `dataTransfer`.
2. Each column: on `dragover` `preventDefault()` (to allow drop) + add a `.drag-over` highlight class; on `drop`, read the id and the column's `data-status`.
3. On drop, `fetch('/tasks/<id>/move', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({status})})`. On success, move the card in the DOM (optimistic); on failure, reload.
4. Progressive enhancement: keep a plain status `<select>` in the edit form so the board still works without JS and for accessibility/keyboard users.

*Optional upgrade path:* if smooth reordering-within-column matters, swap in **SortableJS** (single vendored file, still no build step). Start with native DnD — it satisfies the requirement with no new dependency.

---

## 8. Filtering (assignee, priority, status)

Do it **server-side via query params** so it composes with the board render and survives reloads/bookmarks:

```
GET /sprints/<id>/board?assignee=3&priority=High&status=In%20Progress
```

- The board route reads `request.args`, passes them into `list_tasks(...)`, which builds a `WHERE` clause dynamically from **only the provided** filters (still parametrized — append `?` placeholders, never string-interpolate values).
- Render the filter bar as a small `GET` form (dropdowns for assignee/priority/status + "Clear"). Selecting re-requests the page with the params. No JS needed; the same params can later drive a `fetch` refresh if desired.
- `status` filter narrows which columns show cards — useful with assignee/priority to answer "what High-priority work is assigned to Sam and still in progress?"

---

## 9. Suggested Build Order (milestones)

1. **Fix what's broken first** (fast wins, unblocks the rest): reconcile the failing flash-message test, delete or repair `services.py`, remove the dead `app.js` `<script>` *or* create the file, correct the README `migrate-db` claim. Get to a green `pytest`.
2. **Schema + repository:** add `users` + `tasks` to `schema.sql`, write task repository functions, seed a couple of users for local testing.
3. **Auth:** signup/login/logout, `login_required`, `g.user`, `SECRET_KEY` from env.
4. **Task CRUD:** forms + routes + templates, tasks tagged to a sprint.
5. **Board render:** three columns grouped by status, real `get_sprint_progress` backed by task counts (replace the zero stub; wire the sprint/dashboard progress bars that already exist in the templates).
6. **Drag-and-drop:** `app.js` + `/tasks/<id>/move`.
7. **Filters:** query-param filtering + filter bar.

Each milestone is demoable on its own and keeps the app runnable throughout.

---

## 10. Testing

The existing `tests/` structure (pytest, `tmp_path` DB, `client`, `make_project`, `make_sprint` fixtures) is a good pattern — extend it:

- `make_user` / logged-in `client` fixtures.
- Auth: signup creates a hashed (not plaintext) row; login rejects wrong password; `login_required` redirects anonymous users.
- Task CRUD: create tags the right sprint; validation rejects bad priority/status/date.
- **`/tasks/<id>/move`**: valid status → persisted; invalid status → rejected (no DB change). This is the highest-value test — it guards the board's core interaction.
- Filters: `list_tasks` with each filter returns the right subset.
- Keep every new SQL query parametrized and add one test asserting a `'; DROP`-style title is stored literally, not executed.

---

## 11. Risks / Non-Goals

- **Non-goals (keep it minimal):** no OAuth/SSO, no real-time multi-user sync, no roles/permissions beyond "logged in," no email, no per-column WIP limits.
- **Risks:** (1) status strings must stay identical across DB `CHECK`, Python constant, template `data-status`, and JS — centralize them. (2) Drag-and-drop without a JS fallback locks out keyboard users — keep the status `<select>`. (3) SQLite + threaded dev server is fine for a class demo but not for concurrent production writes — acceptable here.
