"""empty message

Revision ID: daf3d0ebffc4
Revises: 
Create Date: 2020-06-07 01:03:07.790960

"""
import re
import os

from alembic import op
import sqlalchemy as sa
from pathlib import Path
from datetime import datetime



# revision identifiers, used by Alembic.
revision = 'daf3d0ebffc4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=20), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('meals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('picture', sa.String(length=100), nullable=True),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.Column('total_payment', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('address', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ordered_meals',
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('meal_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['meal_id'], ['meals.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], )
    )
    # ### end Alembic commands ###

    lst_categories = []
    with open("categories.tsv", encoding='utf-8') as file:
        next(file)  # for ignoring 1st row
        for line in file:
            lst_temp = re.split(r"\t+", line)
            lst_categories.append({"id": lst_temp[0], "title": lst_temp[1],
                                   "date_created": datetime.utcnow()})

    table_categories = sa.table("categories",
                                sa.Column('id', sa.Integer()),
                                sa.Column('title', sa.String()),
                                sa.Column('date_created', sa.DateTime()))

    op.bulk_insert(table_categories, lst_categories)


    lst_meals = []
    with open("meals.tsv", encoding='utf-8') as file:
        next(file)  # for ignoring 1st row
        for line in file:
            lst_temp = re.split(r"\t+", line)
            lst_meals.append({"id": lst_temp[0], "title": lst_temp[1], "price": lst_temp[2],
                              "description": lst_temp[3], "picture": lst_temp[4],
                              "category_id": lst_temp[5], "date_created": datetime.utcnow()})

    table_meals = sa.table("meals",
                           sa.Column('id', sa.Integer()),
                           sa.Column('title', sa.String()),
                           sa.Column('price', sa.Integer()),
                           sa.Column('description', sa.Text()),
                           sa.Column('picture', sa.String()),
                           sa.Column('category_id', sa.Integer()),
                           sa.Column('date_created', sa.DateTime()))

    op.bulk_insert(table_meals, lst_meals)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ordered_meals')
    op.drop_table('orders')
    op.drop_table('meals')
    op.drop_table('customers')
    op.drop_table('categories')
    # ### end Alembic commands ###
