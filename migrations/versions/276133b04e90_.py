"""empty message

Revision ID: 276133b04e90
Revises: 75719b64908d
Create Date: 2020-02-23 13:54:11.547325

"""

# revision identifiers, used by Alembic.
revision = '276133b04e90'
down_revision = '75719b64908d'

from alembic import op
import sqlalchemy as sa
import citext
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('series', sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('serieschanges', sa.Column('extra_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('serieschanges', 'extra_metadata')
    op.drop_column('series', 'extra_metadata')
    # ### end Alembic commands ###
