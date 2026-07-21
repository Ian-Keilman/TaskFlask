from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask

from .db import close_db, init_db_command, migrate_db_command


PACIFIC_TIME = ZoneInfo("America/Los_Angeles")


def format_datetime(value):
    """Format an ISO timestamp for concise, human-readable display."""
    if not value:
        return "Unknown"

    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return value

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    local_time = parsed.astimezone(PACIFIC_TIME)
    return local_time.strftime("%b %d, %Y at %I:%M %p %Z").replace(" 0", " ")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=str(Path(app.instance_path) / "taskflask.sqlite"),
    )

    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    from . import routes

    app.register_blueprint(routes.bp)
    app.add_template_filter(format_datetime, "friendly_datetime")

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(migrate_db_command)

    return app
