"""empty message

Revision ID: 28d5f385d913
Revises: 13975a13720f
Create Date: 2017-08-02 21:12:29.038092

"""

# revision identifiers, used by Alembic.
revision = '28d5f385d913'
down_revision = '13975a13720f'

from alembic import op
import sqlalchemy as sa
import citext


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('series', sa.Column('rating_count', sa.Integer(), nullable=True))
    op.add_column('serieschanges', sa.Column('rating_count', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('serieschanges', 'rating_count')
    op.drop_column('series', 'rating_count')
    ### end Alembic commands ###
