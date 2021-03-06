"""empty message

Revision ID: ff3d74ef531e
Revises: 6e4c83c81d6f
Create Date: 2017-08-02 22:19:35.980186

"""

# revision identifiers, used by Alembic.
revision = 'ff3d74ef531e'
down_revision = '6e4c83c81d6f'

from alembic import op
import sqlalchemy as sa
import citext


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_releases_srcurl'), 'releases', ['srcurl'], unique=False)
    op.create_index(op.f('ix_serieschanges_srccol_changetime'), 'serieschanges', ['srccol', 'changetime'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_releases_srcurl'), table_name='releases')
    ### end Alembic commands ###
