"""game owned role and rating sets

Revision ID: adea2bb21758
Revises: 2eaa9c8261c3
Create Date: 2026-07-28 17:21:14.337297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adea2bb21758'
down_revision: Union[str, Sequence[str], None] = '2eaa9c8261c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('DELETE FROM custom_rating_table')
    op.execute('DELETE FROM server_game')
    op.execute('DELETE FROM game_role_table')
    op.execute('DELETE FROM rating_table')
    op.execute('DELETE FROM role_set_table')
    op.execute('DELETE FROM rating_set_table')
    op.execute('DELETE FROM game_table')

    op.add_column('game_table', sa.Column('server_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('game_table_server_id_fkey', 'game_table', 'server_table',
                           ['server_id'], ['id'], ondelete='CASCADE')
    op.alter_column('game_table', 'icon_id', existing_type=sa.Uuid(), nullable=True)
    op.alter_column('game_table', 'banner_id', existing_type=sa.Uuid(), nullable=True)
    op.drop_constraint('game_table_name_key', 'game_table', type_='unique')
    op.create_unique_constraint('uq_game_server_name', 'game_table', ['server_id', 'name'])
    op.create_index('uq_game_global_name', 'game_table', ['name'], unique=True,
                     postgresql_where=sa.text('server_id IS NULL'))

    op.drop_column('role_set_table', 'server_id')      # drops its unnamed FK with the column
    op.drop_column('role_set_table', 'is_global')
    op.add_column('role_set_table', sa.Column('game_id', sa.Uuid(), nullable=False))
    op.create_foreign_key('role_set_table_game_id_fkey', 'role_set_table', 'game_table',
                           ['game_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_role_set_game', 'role_set_table', ['game_id'])

    op.drop_column('rating_set_table', 'server_id')
    op.drop_column('rating_set_table', 'is_global')
    op.add_column('rating_set_table', sa.Column('game_id', sa.Uuid(), nullable=False))
    op.create_foreign_key('rating_set_table_game_id_fkey', 'rating_set_table', 'game_table',
                           ['game_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('uq_rating_set_game', 'rating_set_table', ['game_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DELETE FROM custom_rating_table')
    op.execute('DELETE FROM server_game')
    op.execute('DELETE FROM game_role_table')
    op.execute('DELETE FROM rating_table')
    op.execute('DELETE FROM role_set_table')
    op.execute('DELETE FROM rating_set_table')
    op.execute('DELETE FROM game_table')

    op.drop_constraint('role_set_table_game_id_fkey', 'role_set_table', type_='foreignkey')
    op.drop_constraint('uq_role_set_game', 'role_set_table', type_='unique')
    op.drop_column('role_set_table', 'game_id')

    op.drop_constraint('rating_set_table_game_id_fkey', 'rating_set_table', type_='foreignkey')
    op.drop_constraint('uq_rating_set_game', 'rating_set_table', type_='unique')
    op.drop_column('rating_set_table', 'game_id')

    op.drop_index('uq_game_global_name', table_name='game_table')
    op.drop_constraint('uq_game_server_name', 'game_table', type_='unique')
    op.drop_constraint('game_table_server_id_fkey', 'game_table', type_='foreignkey')
    op.drop_column('game_table', 'server_id')

    op.add_column('role_set_table', sa.Column('is_global', sa.Boolean(), nullable=False))
    op.add_column('role_set_table', sa.Column('server_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'role_set_table', 'server_table', ['server_id'], ['id'], ondelete='CASCADE')

    op.add_column('rating_set_table', sa.Column('is_global', sa.Boolean(), nullable=False))
    op.add_column('rating_set_table', sa.Column('server_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'rating_set_table', 'server_table', ['server_id'], ['id'], ondelete='CASCADE')

    op.create_unique_constraint('game_table_name_key', 'game_table', ['name'])
    op.alter_column('game_table', 'icon_id', existing_type=sa.Uuid(), nullable=False)
    op.alter_column('game_table', 'banner_id', existing_type=sa.Uuid(), nullable=False)
