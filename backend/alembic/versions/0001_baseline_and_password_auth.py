"""Create the current schema and add password authentication safely."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from app.core.database import Base
import app.core.init_db  # noqa: F401

revision = "0001_baseline_and_password_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    Base.metadata.create_all(bind=bind)
    if "users" in existing_tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "password_hash" not in user_columns:
            op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    # This baseline intentionally has no destructive downgrade.
    pass
