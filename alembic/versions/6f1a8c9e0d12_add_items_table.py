"""add_items_table

Revision ID: 6f1a8c9e0d12
Revises: 5bea465ff3f9
Create Date: 2026-09-09 13:46:00.000000

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f1a8c9e0d12'
down_revision: str | None = '5bea465ff3f9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent', sa.Integer(), nullable=True),
        sa.Column('create_time', sa.BigInteger(), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(['parent'], ['items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_items_parent'), ['parent'], unique=False)
        batch_op.create_index(batch_op.f('ix_items_type'), ['type'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_items_type'))
        batch_op.drop_index(batch_op.f('ix_items_parent'))

    op.drop_table('items')
