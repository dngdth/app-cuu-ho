"""Add saved ensemble diagnostics without changing existing rescue requests."""
from alembic import op
import sqlalchemy as sa

revision = "20261121_prediction"
down_revision = "reset_db_2025"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("rescue_prediction"):
        op.create_table(
            "rescue_prediction",
            sa.Column("rescue_request_id", sa.Integer(), sa.ForeignKey("rescue_request.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("details", sa.JSON(), nullable=False),
            sa.Column("created_date", sa.DateTime()),
        )


def downgrade():
    op.drop_table("rescue_prediction")
