"""Add exercises table.

Revision ID: 20261106_0003
Revises: 20261026_0002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261106_0003"
down_revision: Union[str, None] = "20261026_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("muscle_group", sa.String(), nullable=True),
        sa.Column("equipment", sa.String(), nullable=True),
    )
    op.create_index("ix_exercises_name", "exercises", ["name"])
    op.create_index("ix_exercises_muscle_group", "exercises", ["muscle_group"])
    op.create_index("ix_exercises_equipment", "exercises", ["equipment"])


def downgrade() -> None:
    op.drop_index("ix_exercises_equipment", table_name="exercises")
    op.drop_index("ix_exercises_muscle_group", table_name="exercises")
    op.drop_index("ix_exercises_name", table_name="exercises")
    op.drop_table("exercises")
