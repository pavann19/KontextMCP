"""Explicit migration operations; verification never creates application tables."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import text
from app.db.models import Base

ROOT = Path(__file__).resolve().parents[2]


def configuration(connection=None):
    config = Config()
    config.set_main_option("script_location", str(ROOT / "migrations"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def verify_schema(connection):
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    if set(context.get_current_heads()) != set(ScriptDirectory.from_config(configuration()).get_heads()):
        raise RuntimeError("Database migration required; run python -m scripts.migrate_db upgrade.")
    if compare_metadata(context, Base.metadata):
        raise RuntimeError("Database schema drift detected; review migrations before starting the service.")


def upgrade_schema(connection, target="head"):
    # Serialize independent migrators for this database, not application traffic.
    if connection.dialect.name == "postgresql":
        connection.execute(text("SELECT pg_advisory_xact_lock(739124608)"))
    command.upgrade(configuration(connection), target)
