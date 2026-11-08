"""Database session manager supporting SQLite and PostgreSQL (P6.5)."""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.models import Base

# Clean sqlite / postgres connection url
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite+aiosqlite:"):
    db_url = db_url.replace("sqlite+aiosqlite:", "sqlite:")
elif db_url.startswith("postgresql://"):
    # SQLAlchemy 2.1 changed the implicit default to psycopg 3. This project
    # installs the synchronous psycopg2 driver, so select it explicitly.
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

connect_args = {}
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgresql"):
    connect_args = {"connect_timeout": 5, "options": "-c statement_timeout=15000 -c lock_timeout=10000"}

engine = create_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

def init_db() -> None:
    """Production verifies the migrated schema; development can create fixtures."""
    if settings.DATABASE_SCHEMA_MODE == "verify":
        from app.db.migrations import verify_schema
        with engine.connect() as connection:
            verify_schema(connection)
    else:
        Base.metadata.create_all(bind=engine)

def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for non-FastAPI script and tool execution."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
