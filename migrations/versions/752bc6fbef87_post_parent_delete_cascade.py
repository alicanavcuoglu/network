"""post parent delete cascade

Revision ID: 752bc6fbef87
Revises: 34a6762cae2f
Create Date: 2024-11-30 15:04:40.319638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '752bc6fbef87'
down_revision = '34a6762cae2f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_constraint('post_parent_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'post', ['parent_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('post_parent_id_fkey', 'post', ['parent_id'], ['id'])

    # ### end Alembic commands ###
