"""update notification enum values

Revision ID: cd996378d79a
Revises: 342d86f18580
Create Date: 2024-12-01 00:54:46.219124

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd996378d79a'
down_revision = '342d86f18580'
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary "old" type, convert and drop the temp type
    op.execute("ALTER TYPE notificationenum RENAME TO notificationenum_old;")
    op.execute("CREATE TYPE notificationenum AS ENUM ('friend_request', 'friend_accepted', 'post_like', 'post_comment', 'post_share', 'comment_like', 'group_invite', 'invite_accepted', 'admin_promotion');")
    op.execute("ALTER TABLE notification ALTER COLUMN notification_type TYPE notificationenum USING notification_type::text::notificationenum;")
    op.execute("DROP TYPE notificationenum_old;")

def downgrade():
    # Create a temporary "new" type, convert and drop the temp type
    op.execute("ALTER TYPE notificationenum RENAME TO notificationenum_new;")
    op.execute("CREATE TYPE notificationenum AS ENUM ('friend_request', 'friend_accepted', 'post_like', 'post_comment', 'post_share', 'comment_like');")
    op.execute("ALTER TABLE notification ALTER COLUMN notification_type TYPE notificationenum USING notification_type::text::notificationenum;")
    op.execute("DROP TYPE notificationenum_new;")
