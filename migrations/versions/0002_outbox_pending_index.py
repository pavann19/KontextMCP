"""Index pending-delivery scans without changing stored audit history."""
from alembic import op

revision = "0002_outbox_pending_index"
down_revision = "0001_baseline"
branch_labels = depends_on = None


def upgrade():
    op.create_index("ix_audit_outbox_delivery_created", "audit_outbox", ["delivered_at", "created_at"])


def downgrade():
    op.drop_index("ix_audit_outbox_delivery_created", table_name="audit_outbox")
