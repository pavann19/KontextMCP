import pytest
from app.config import Settings


def production(**updates):
    values = dict(ENVIRONMENT="production", DEBUG=False, API_KEYS={"k"*40: {
        "username": "operator", "role": "compliance_officer", "department": "legal"}},
        AUDIT_CHECKPOINT_KEY="a"*40, DATABASE_URL="postgresql+psycopg2://operator:fixture-long-password@localhost/db",
        DATABASE_SCHEMA_MODE="verify", QDRANT_PREFER_LOCAL=False, QDRANT_HOST="qdrant",
        HTTP_ALLOWED_HOSTS=["localhost"], ALLOWED_ORIGINS=[])
    return Settings(_env_file=None, **{**values, **updates})


@pytest.mark.parametrize("changes", [{"DEBUG": True}, {"API_KEYS": {}}, {"AUDIT_CHECKPOINT_KEY": "short"},
    {"DATABASE_URL": "sqlite:///fixture.db"}, {"DATABASE_SCHEMA_MODE": "create"},
    {"QDRANT_PREFER_LOCAL": True}, {"HTTP_ALLOWED_HOSTS": ["*"]}, {"ALLOWED_ORIGINS": ["*"]},
    {"ENABLE_PROMPT_GUARD": False}, {"DATABASE_URL": "postgresql://postgres:postgres@localhost/db"}])
def test_production_refuses_unsafe_configuration(changes):
    with pytest.raises(RuntimeError, match="Unsafe production configuration"):
        production(**changes).validate_runtime()


def test_complete_production_configuration_is_accepted():
    production().validate_runtime()
