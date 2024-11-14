from flask import session
from sqlalchemy import case, select

from app.services import db
from app.models import Message, Post, User


# Friends of user
def get_friends(user_id):
    user = db.get_or_404(User, user_id)

    return user.friends


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


def get_posts(user_id):
    posts = (
        Post.query.filter(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .all()
    )

    return posts


def get_user_by_username(username, posts=False):
    query = select(User).filter_by(username=username, is_completed=True)

    if posts:
        query.outerjoin(User.posts)

    return db.first_or_404(query)


# TODO: Get user's groups
def get_groups(user_id):
    # groups = select(Group).filter_by(user_id in members)
    ...

    # return db.first_or_404(query)
