from alembic import context
from app.db.models import Base

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Use python -m scripts.migrate_db; explicit connection management is required.")
context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
with context.begin_transaction():
    context.run_migrations()
