"""add_code_fields_to_strategies

Revision ID: c2deb7c267b4
Revises: 202507241144
Create Date: 2025-07-26 12:24:14.931720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2deb7c267b4'
down_revision: Union[str, Sequence[str], None] = '202507241144'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add code and code_language fields to strategies table."""
    # Add code field
    op.add_column('strategies', sa.Column('code', sa.Text(), nullable=True))
    
    # Add code_language field with default value
    op.add_column('strategies', sa.Column('code_language', sa.String(length=50), nullable=False, server_default='python'))
    
    # Remove the server default after adding the column
    op.alter_column('strategies', 'code_language', server_default=None)


def downgrade() -> None:
    """Remove code and code_language fields from strategies table."""
    op.drop_column('strategies', 'code_language')
    op.drop_column('strategies', 'code')
