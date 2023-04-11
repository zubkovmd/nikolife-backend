"""add image to category

Revision ID: 2023_04_11_1929
Revises: 2023_04_11_0038
Create Date: 2023-04-11 19:29:21.243803

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2023_04_11_1929'
down_revision = '2023_04_11_0038'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('recipe_categories', sa.Column('image', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recipe_categories', 'image')
    # ### end Alembic commands ###