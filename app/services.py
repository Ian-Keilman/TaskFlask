from .forms import VALID_STATUSES


def _value(row, key):
    try:
        return row[key]
    except (KeyError, TypeError):
        return getattr(row, key, None)


def calculate_progress(tasks):
    """Return simple sprint progress counts for a list of task rows."""
    counts = {status: 0 for status in VALID_STATUSES}

    for task in tasks:
        status = _value(task, "status")
        if status in counts:
            counts[status] += 1

    return progress_from_counts(
        sum(counts.values()),
        counts["To Do"],
        counts["In Progress"],
        counts["Done"],
    )


def progress_from_counts(total, to_do, in_progress, done):
    """Build the progress shape used by projects and sprints."""
    total = int(total or 0)
    to_do = int(to_do or 0)
    in_progress = int(in_progress or 0)
    done = int(done or 0)

    return {
        "total": total,
        "to_do": to_do,
        "in_progress": in_progress,
        "done": done,
        "percent_complete": round((done / total) * 100) if total else 0,
    }


def with_progress(row):
    """Add display-ready progress fields to a query row that has task counts."""
    item = dict(row)
    item.update(
        progress_from_counts(
            item.get("task_count"),
            item.get("to_do_count"),
            item.get("in_progress_count"),
            item.get("done_count"),
        )
    )
    return item