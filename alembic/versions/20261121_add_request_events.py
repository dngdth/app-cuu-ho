"""Add human review history without altering existing requests."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_events"
down_revision = "20261121_prediction"
branch_labels = None
depends_on = None


def upgrade():
    if not sa.inspect(op.get_bind()).has_table("rescue_request_event"):
        op.create_table("rescue_request_event",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("rescue_request_id", sa.Integer(), sa.ForeignKey("rescue_request.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("actor", sa.String(100), nullable=False),
            sa.Column("note", sa.String(2000), nullable=False),
            sa.Column("changes", sa.JSON(), nullable=False))
        op.create_index("ix_rescue_request_event_rescue_request_id", "rescue_request_event", ["rescue_request_id"])


def downgrade():
    op.drop_table("rescue_request_event")
