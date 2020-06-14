"""empty message

Revision ID: 7a9337138149
Revises: daf3d0ebffc4
Create Date: 2020-06-13 00:48:28.636996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a9337138149'
down_revision = 'daf3d0ebffc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ordered_meals',
                  sa.Column('amount_meal', sa.Integer(), nullable=False, server_default="1"))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ordered_meals', 'amount_meal')
    # ### end Alembic commands ###