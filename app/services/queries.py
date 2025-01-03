from sqlalchemy import and_, case, func, or_, select

from app.models import (
    Group,
    GroupType,
    Message,
    Post,
    User,
    friends_table,
    group_admins,
    group_members,
    received_requests_table,
)
from app.services import db


# Friends of user
def get_friends(
    user_id,
    page=1,
    per_page=10,
):
    query = (
        select(User)
        .join(friends_table, friends_table.c.friend_id == User.id)
        .filter(friends_table.c.user_id == user_id)
    )

    return db.paginate(query, page=page, per_page=per_page)


# Friend requests for user
def get_requests(user_id):
    requests = (
        db.session.execute(
            select(User)
            .join(
                received_requests_table, received_requests_table.c.request_id == User.id
            )
            .filter(received_requests_table.c.user_id == user_id)
        )
        .scalars()
        .all()
    )

    return requests


# Errors fixed by ChatGPT
# Messages between current user and users
def get_latest_conversations(user_id):
    # Define user1_id and user2_id without LEAST and GREATEST
    latest_message_subquery = (
        db.session.query(
            case(
                (Message.sender_id < Message.recipient_id, Message.sender_id),
                else_=Message.recipient_id,
            ).label("user1_id"),
            case(
                (Message.sender_id > Message.recipient_id, Message.sender_id),
                else_=Message.recipient_id,
            ).label("user2_id"),
            db.func.max(Message.created_at).label("latest_created_at"),
        )
        .filter((Message.sender_id == user_id) | (Message.recipient_id == user_id))
        .group_by("user1_id", "user2_id")
        .subquery()
    )

    # Join with Message to get the full Message objects
    latest_messages = (
        db.session.query(Message)
        .join(
            latest_message_subquery,
            db.or_(
                db.and_(
                    Message.sender_id == latest_message_subquery.c.user1_id,
                    Message.recipient_id == latest_message_subquery.c.user2_id,
                ),
                db.and_(
                    Message.sender_id == latest_message_subquery.c.user2_id,
                    Message.recipient_id == latest_message_subquery.c.user1_id,
                ),
            )
            & (Message.created_at == latest_message_subquery.c.latest_created_at),
        )
        .order_by(Message.created_at.desc())
        .all()
    )

    return latest_messages


# Fetch messages exchanged between the current user and the other user
def get_conversation(user_id, other_user_id):
    messages = (
        Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == other_user_id))
            | ((Message.sender_id == other_user_id) & (Message.recipient_id == user_id))
        )
        .order_by(Message.created_at.asc())
        .all()
    )

    return messages


def start_conversation(): ...


# Return unread messages
def has_unread_messages(user_id):
    # Count the unread messages for the current user
    unread_count = (
        db.session.execute(
            select(Message.id).where(
                (Message.recipient_id == user_id) & (Message.is_read == False)
            )
        ).scalar()
        or 0
    )

    return unread_count > 0


def get_user_by_username(username, posts=False):
    query = select(User).filter_by(username=username, is_completed=True)

    if posts:
        query.outerjoin(User.posts)

    return db.first_or_404(query)


def get_users(page=1, per_page=10, search_query=None, get_friends=False, user_id=None):
    query = select(User).filter_by(is_completed=True)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.where(
            or_(
                User.name.ilike(search_term),
                User.surname.ilike(search_term),
                User.username.ilike(search_term),
                # For full name
                func.concat(User.name, " ", User.surname).ilike(search_term),
            )
        )

    if get_friends and user_id:
        query = query.join(friends_table, friends_table.c.friend_id == User.id).filter(
            friends_table.c.user_id == user_id
        )

    return db.paginate(query, page=page, per_page=per_page)


def get_user_posts(page=1, per_page=10, user_id=None):
    query = (
        select(Post)
        .join(Post.user)
        .filter(
            Post.user_id == user_id,
        )
        .order_by(Post.created_at.desc())
    )

    return db.paginate(query, page=page, per_page=per_page)


def get_community_posts(
    page=1, per_page=10, user_id=None, friends=None, tag_pattern=None
):
    query = select(Post).join(Post.user)

    user_groups = select(Group.id).where(
        or_(
            Group.owner_id == user_id,
            Group.id.in_(
                select(group_admins.c.group_id).where(group_admins.c.user_id == user_id)
            ),
            Group.id.in_(
                select(group_members.c.group_id).where(
                    group_members.c.user_id == user_id
                )
            ),
        )
    )

    group_filters = or_(
        Post.group_id.in_(user_groups),
        and_(
            Post.group_id.in_(
                select(Group.id).where(Group.group_type == GroupType.PUBLIC)
            ),
            or_(
                Post.user_id == user_id,
                Post.user_id.in_([friend.id for friend in friends]),
                User.is_private == False,
            ),
        ),
    )

    user_filters = and_(
        Post.group_id.is_(None),
        or_(
            Post.user_id == user_id,
            Post.user_id.in_([friend.id for friend in friends]),
            User.is_private == False,
        ),
    )

    all_filters = or_(group_filters, user_filters)

    if tag_pattern:
        query = query.filter(and_(all_filters, Post.content.ilike(tag_pattern)))
    else:
        query = query.filter(all_filters)

    query = query.order_by(Post.created_at.desc())

    return db.paginate(query, page=page, per_page=per_page)


def get_posts(
    page=1,
    per_page=10,
    user_id=None,
    friends=None,
):
    query = select(Post).join(Post.user)

    user_groups = select(Group.id).where(
        or_(
            Group.owner_id == user_id,
            Group.id.in_(
                select(group_admins.c.group_id).where(group_admins.c.user_id == user_id)
            ),
            Group.id.in_(
                select(group_members.c.group_id).where(
                    group_members.c.user_id == user_id
                )
            ),
        )
    )

    filters = or_(
        and_(
            or_(
                Post.user_id == user_id,
                Post.user_id.in_([friend.id for friend in friends]),
            )
        ),
        Post.group_id.in_(user_groups),
    )

    query = query.where(filters).order_by(Post.created_at.desc())

    return db.paginate(query, page=page, per_page=per_page)


def get_groups(page=1, per_page=10, search_query=None, user_id=None):
    query = select(Group)

    if user_id:
        query = query.where(
            or_(
                Group.owner_id == user_id,
                Group.id.in_(
                    select(group_admins.c.group_id).where(
                        group_admins.c.user_id == user_id
                    )
                ),
                Group.id.in_(
                    select(group_members.c.group_id).where(
                        group_members.c.user_id == user_id
                    )
                ),
            )
        )

    if search_query:
        search_term = f"%{search_query}%"
        query = query.where(
            or_(
                Group.name.ilike(search_term),
                Group.about.ilike(search_term),
            )
        )

    return db.paginate(
        query.order_by(Group.created_at.desc()), page=page, per_page=per_page
    )


def get_users_groups(
    page=1,
    per_page=10,
    user_id=None,
):
    query = (
        select(Group)
        .filter(
            or_(
                Group.owner_id == user_id,
                Group.id.in_(
                    select(group_admins.c.group_id).filter(
                        group_admins.c.user_id == user_id
                    )
                ),
                Group.id.in_(
                    select(group_members.c.group_id).filter(
                        group_members.c.user_id == user_id
                    )
                ),
            )
        )
        .order_by(Group.created_at.desc())
    )

    return db.paginate(query, page=page, per_page=per_page)


def get_group_posts(
    page=1,
    per_page=10,
    group_id=None,
):
    query = (
        select(Post)
        .join(Post.group)
        .filter(Post.group_id == group_id)
        .order_by(Post.created_at.desc())
    )

    return db.paginate(query, page=page, per_page=per_page)


def get_group_admins(
    page=1,
    per_page=10,
    group_id=None,
):
    query = select(User).join(group_admins).filter(group_admins.c.group_id == group_id)

    return db.paginate(query, page=page, per_page=per_page)


def get_group_members(
    page=1,
    per_page=10,
    group_id=None,
):
    query = (
        select(User).join(group_members).filter(group_members.c.group_id == group_id)
    )

    return db.paginate(query, page=page, per_page=per_page)


def get_users_to_invite(page=1, per_page=10, search_query=None, group_id=None):
    query = select(User).filter(
        User.is_completed == True,
        User.id.not_in(
            select(group_members.c.user_id).filter(group_members.c.group_id == group_id)
        ),
        User.id.not_in(
            select(group_admins.c.user_id).filter(group_admins.c.group_id == group_id)
        ),
        User.id
        != select(Group.owner_id).filter(Group.id == group_id).scalar_subquery(),
    )

    if search_query:
        search_term = f"%{search_query}%"
        query = query.where(
            or_(
                User.name.ilike(search_term),
                User.surname.ilike(search_term),
                User.username.ilike(search_term),
                # For full name
                func.concat(User.name, " ", User.surname).ilike(search_term),
            ),
        )

    return db.paginate(query, page=page, per_page=per_page)
