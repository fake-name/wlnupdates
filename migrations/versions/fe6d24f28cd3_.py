"""empty message

Revision ID: fe6d24f28cd3
Revises: 355ab81681f
Create Date: 2016-05-15 20:15:42.379051

"""

# revision identifiers, used by Alembic.
revision = 'fe6d24f28cd3'
down_revision = '355ab81681f'

from alembic import op
import sqlalchemy as sa
import citext


def upgrade():
    op.add_column('releases', sa.Column('fragment', sa.Float(), nullable=True))
    op.add_column('releaseschanges', sa.Column('fragment', sa.Float(), nullable=True))

    op.create_index(op.f('ix_releases_fragment'), 'releases', ['fragment'], unique=False)
    op.create_index(op.f('ix_releaseschanges_fragment'), 'releaseschanges', ['fragment'], unique=False)
    ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_releaseschanges_fragment'), table_name='releaseschanges')
    op.drop_index(op.f('ix_releases_fragment'), table_name='releases')

    op.drop_column('releaseschanges', 'fragment')
    op.drop_column('releases', 'fragment')
    ### end Alembic commands ###
