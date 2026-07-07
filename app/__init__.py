from pathlib import Path

from flask import Flask

from .db import close_db, init_db_command


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

    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

    return app
