import pytest
from sqlalchemy import create_engine, inspect, text
from app.db.models import Base
from app.db.migrations import upgrade_schema, verify_schema


def test_fresh_upgrade_and_index_evolution_preserve_records(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "migration.db").as_posix())
    with engine.begin() as connection:
        upgrade_schema(connection, "0001_baseline")
        connection.execute(text("INSERT INTO users(username,full_name,role,department) VALUES ('fixture','Fixture','developer','engineering')"))
        with pytest.raises(RuntimeError, match="migration required"):
            verify_schema(connection)
        upgrade_schema(connection)
        verify_schema(connection)
        upgrade_schema(connection)
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1
        connection.execute(text("DROP INDEX ix_audit_outbox_delivery_created"))
        with pytest.raises(RuntimeError, match="drift"):
            verify_schema(connection)
    engine.dispose()


def test_verification_never_silently_adopts_legacy_schema(tmp_path):
    engine = create_engine("sqlite:///" + (tmp_path / "legacy.db").as_posix())
    Base.metadata.create_all(engine)
    before = inspect(engine).get_table_names()
    with engine.connect() as connection:
        with pytest.raises(RuntimeError, match="migration required"):
            verify_schema(connection)
    assert inspect(engine).get_table_names() == before
    engine.dispose()
