# TaskFlask

TaskFlask is a server-rendered Scrum tracker for projects, sprints, and tasks.
It includes a three-column task board, required numeric story-point estimates, safe
Markdown task descriptions, story-point progress, and a cumulative project
burnup chart that combines every sprint.

## Install and Run Locally

From the project folder, create a virtual environment.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the local database on a first run:

```bash
python -m flask --app run init-db
```

Run the app:

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Design System

TaskFlask uses shared color, typography, spacing, shape, and interaction tokens
defined in `app/static/style.css`. Reusable buttons, cards, forms, statuses,
priorities, and accessibility states are demonstrated at
[http://127.0.0.1:5000/design-system](http://127.0.0.1:5000/design-system).

## Existing Local Database

To update an existing local database without resetting its data:

```bash
python -m flask --app run migrate-db
```

To reset the local database:

```bash
python -m flask --app run init-db
```

## Demo With Your Own Project Data

For a realistic project review, create a TaskFlask project for the team's real
development work, then add the actual course sprints and tasks from the sprint
documents. Preserve the real task titles, sprint assignments, story-point
estimates, added dates, completion dates, and assignees. The project page will
then produce one cumulative burnup chart from that data, while the sprint boards
show the underlying work.

TaskFlask does not invent or silently seed course records. Enter or import only
the team's verified sprint information so the demonstration remains accurate.