"""Add isolated operations tables. Does not reset or alter rescue source records."""
from alembic import op
from app.db.database import Base
import app.models  # register additive table metadata

revision = "20261122_operations"
down_revision = "20261121_events"
branch_labels = None
depends_on = None

TABLES = ("api_counter", "provider_cache", "app_user", "user_session", "login_throttle", "processing_job")


def upgrade():
    for name in TABLES:
        Base.metadata.tables[name].create(op.get_bind(), checkfirst=True)


def downgrade():
    for name in reversed(TABLES):
        Base.metadata.tables[name].drop(op.get_bind(), checkfirst=True)
