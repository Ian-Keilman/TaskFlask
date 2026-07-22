from .forms import VALID_STATUSES


def _value(row, key):
    try:
        return row[key]
    except (KeyError, TypeError):
        return getattr(row, key, None)


def calculate_progress(tasks):
    """Return task counts and story-point progress for a task collection."""
    counts = {status: 0 for status in VALID_STATUSES}
    total_points = 0
    completed_points = 0

    for task in tasks:
        status = _value(task, "status")
        if status in counts:
            counts[status] += 1
        story_points = int(_value(task, "story_points") or 0)
        total_points += story_points
        if status == "Done":
            completed_points += story_points

    return progress_from_counts(
        sum(counts.values()),
        counts["To Do"],
        counts["In Progress"],
        counts["Done"],
        total_points,
        completed_points,
    )


def progress_from_counts(
    total,
    to_do,
    in_progress,
    done,
    total_points=0,
    completed_points=0,
):
    """Build count metrics plus a story-point completion percentage."""
    total = int(total or 0)
    to_do = int(to_do or 0)
    in_progress = int(in_progress or 0)
    done = int(done or 0)
    total_points = int(total_points or 0)
    completed_points = int(completed_points or 0)

    return {
        "total": total,
        "to_do": to_do,
        "in_progress": in_progress,
        "done": done,
        "total_points": total_points,
        "completed_points": completed_points,
        "percent_complete": round((completed_points / total_points) * 100)
        if total_points
        else 0,
    }


def with_progress(row):
    """Add display-ready progress fields to a query row with task counts."""
    item = dict(row)
    item.update(
        progress_from_counts(
            item.get("task_count"),
            item.get("to_do_count"),
            item.get("in_progress_count"),
            item.get("done_count"),
            item.get("total_points"),
            item.get("completed_points"),
        )
    )
    return item