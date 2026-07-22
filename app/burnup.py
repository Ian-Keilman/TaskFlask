from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


PACIFIC_TIME = ZoneInfo("America/Los_Angeles")


def _as_date(value):
    if not value:
        return None

    text = str(value)
    try:
        if len(text) == 10:
            return date.fromisoformat(text)

        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(PACIFIC_TIME).date()
    except ValueError:
        return None


def _value(row, key, default=None):
    try:
        value = row[key]
    except (KeyError, TypeError):
        value = getattr(row, key, default)
    return default if value is None else value


def build_burnup_series(sprint, tasks, today=None):
    """Build daily total and completed story-point lines for one sprint."""
    today = today or datetime.now(PACIFIC_TIME).date()
    tasks = list(tasks)

    task_dates = [
        parsed
        for task in tasks
        for parsed in (
            _as_date(_value(task, "added_on")),
            _as_date(_value(task, "created_at")),
            _as_date(_value(task, "updated_at")),
        )
        if parsed
    ]
    sprint_created = _as_date(_value(sprint, "created_at"))
    fallback_start_dates = task_dates + ([sprint_created] if sprint_created else [])
    start = _as_date(_value(sprint, "start_date")) or (
        min(fallback_start_dates) if fallback_start_dates else today
    )
    planned_end = _as_date(_value(sprint, "end_date"))
    latest_activity = max(task_dates) if task_dates else start

    if _value(sprint, "status") == "Active":
        end = max(planned_end or today, today, latest_activity)
    else:
        completed_on = _as_date(_value(sprint, "completed_at"))
        end = max(planned_end or start, completed_on or start, latest_activity)

    if end < start:
        end = start

    points = []
    current = start
    while current <= end:
        total = 0
        completed = 0

        for task in tasks:
            story_points = int(_value(task, "story_points", 0) or 0)
            created_on = (
                _as_date(_value(task, "added_on"))
                or _as_date(_value(task, "created_at"))
                or start
            )

            if created_on <= current:
                total += story_points

            if _value(task, "status") == "Done":
                completed_on = (
                    _as_date(_value(task, "completed_at"))
                    or _as_date(_value(task, "updated_at"))
                    or created_on
                )
                if completed_on <= current:
                    completed += story_points

        points.append(
            {
                "date": current.isoformat(),
                "total": total,
                "completed": completed,
            }
        )
        current += timedelta(days=1)

    total_points = sum(int(_value(task, "story_points", 0) or 0) for task in tasks)
    completed_points = sum(
        int(_value(task, "story_points", 0) or 0)
        for task in tasks
        if _value(task, "status") == "Done"
    )

    return {
        "id": _value(sprint, "id"),
        "name": _value(sprint, "name", "Sprint"),
        "status": _value(sprint, "status", "Active"),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_points": total_points,
        "completed_points": completed_points,
        "percent_complete": round((completed_points / total_points) * 100)
        if total_points
        else 0,
        "points": points,
    }


def build_project_burnup_series(project, sprints, tasks, today=None):
    """Build one cumulative story-point series across every project sprint."""
    today = today or datetime.now(PACIFIC_TIME).date()
    sprints = list(sprints)
    tasks = list(tasks)

    task_added_dates = [
        _as_date(_value(task, "added_on"))
        or _as_date(_value(task, "created_at"))
        for task in tasks
    ]
    task_added_dates = [value for value in task_added_dates if value]
    task_activity_dates = [
        value
        for task in tasks
        for value in (
            _as_date(_value(task, "completed_at")),
            _as_date(_value(task, "updated_at")),
        )
        if value
    ]
    sprint_dates = [
        value
        for sprint in sprints
        for value in (
            _as_date(_value(sprint, "start_date")),
            _as_date(_value(sprint, "created_at")),
        )
        if value
    ]
    project_created = _as_date(_value(project, "created_at"))

    start_candidates = task_added_dates + sprint_dates
    if project_created:
        start_candidates.append(project_created)
    start = min(start_candidates) if start_candidates else today

    end_candidates = [today, start] + task_added_dates + task_activity_dates
    end = max(end_candidates)

    points = []
    current = start
    while current <= end:
        total = 0
        completed = 0

        for task in tasks:
            story_points = int(_value(task, "story_points", 0) or 0)
            added_on = (
                _as_date(_value(task, "added_on"))
                or _as_date(_value(task, "created_at"))
                or start
            )
            if added_on <= current:
                total += story_points

            if _value(task, "status") == "Done":
                completed_on = (
                    _as_date(_value(task, "completed_at"))
                    or _as_date(_value(task, "updated_at"))
                    or added_on
                )
                if completed_on <= current:
                    completed += story_points

        points.append(
            {
                "date": current.isoformat(),
                "total": total,
                "completed": completed,
            }
        )
        current += timedelta(days=1)

    total_points = sum(int(_value(task, "story_points", 0) or 0) for task in tasks)
    completed_points = sum(
        int(_value(task, "story_points", 0) or 0)
        for task in tasks
        if _value(task, "status") == "Done"
    )

    return {
        "project_id": _value(project, "id"),
        "name": _value(project, "name", "Project"),
        "sprint_count": len(sprints),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "total_points": total_points,
        "completed_points": completed_points,
        "percent_complete": round((completed_points / total_points) * 100)
        if total_points
        else 0,
        "points": points,
    }
