import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.extensions import db
from app.utils.time_utils import format_message_time, format_time_ago

# Association table for friends
friends_table = Table(
    "friends",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("friend_id", Integer, ForeignKey("user.id")),
)

# Association table for pending friend requests
pending_requests_table = Table(
    "pending_requests",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("pending_id", Integer, ForeignKey("user.id")),
)

# Association table for received friend requests
received_requests_table = Table(
    "received_requests",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("request_id", Integer, ForeignKey("user.id")),
)

# Association table for group members
group_members = Table(
    "members",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
)

group_admins = Table(
    "admins",
    db.Model.metadata,
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("group_id", Integer, ForeignKey("group.id")),
)


# User model
class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)

    image: Mapped[str] = mapped_column(String(300), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=True)
    surname: Mapped[str] = mapped_column(String(150), nullable=True)
    location: Mapped[str] = mapped_column(String(150), nullable=True)
    about: Mapped[str] = mapped_column(Text, nullable=True)
    working_on: Mapped[str] = mapped_column(String(200), nullable=True)
    interests: Mapped[str] = mapped_column(Text, nullable=True)
    classes: Mapped[str] = mapped_column(Text, nullable=True)
    links: Mapped[str] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)

    # Many-to-Many relationship for friends
    friends: Mapped[List["User"]] = relationship(
        "User",
        secondary=friends_table,
        primaryjoin=id == friends_table.c.user_id,
        secondaryjoin=id == friends_table.c.friend_id,
        backref="friends_with",
    )

    # Many-to-Many relationship for pending friend requests
    pending_requests: Mapped[List["User"]] = relationship(
        "User",
        secondary=pending_requests_table,
        primaryjoin=id == pending_requests_table.c.user_id,
        secondaryjoin=id == pending_requests_table.c.pending_id,
        backref="pending_from",
    )

    # Many-to-Many relationship for received friend requests
    received_requests: Mapped[List["User"]] = relationship(
        "User",
        secondary=received_requests_table,
        primaryjoin=id == received_requests_table.c.user_id,
        secondaryjoin=id == received_requests_table.c.request_id,
        backref="received_from",
    )

    posts: Mapped[List["Post"]] = relationship(
        back_populates="user", cascade="all, delete"
    )

    likes: Mapped[List["Like"]] = relationship(
        back_populates="user", cascade="all, delete"
    )

    # One-to-Many relationship for user's groups
    owned_groups: Mapped[List["Group"]] = relationship(
        back_populates="owner", lazy=True, cascade="all, delete"
    )

    # Many-to-Many relationship for group's admins
    admin_in: Mapped[List["Group"]] = relationship(
        secondary=group_admins, lazy="dynamic", back_populates="admins"
    )

    # Many-to-Many relationship for group's members
    member_in: Mapped[List["Group"]] = relationship(
        secondary=group_members, lazy="dynamic", back_populates="members"
    )

    # Sent invitations
    sent_invitations: Mapped[List["Invitation"]] = relationship(
        foreign_keys="[Invitation.inviter_id]", back_populates="inviter"
    )

    # Received invitations
    received_invitations: Mapped[List["Invitation"]] = relationship(
        foreign_keys="[Invitation.invitee_id]", back_populates="invitee"
    )

    def __repr__(self) -> str:
        return super().__repr__()

    def is_friends(self, user_id):
        return any(friend.id == user_id for friend in self.friends)

    def total_friends(self) -> int:
        return len(self.friends)

    def total_posts(self) -> int:
        return len(self.posts)


# Post model
class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    # Reshare
    parent_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="SET NULL"), nullable=True)
    # Group post
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    shares: Mapped[int] = mapped_column(Integer, default=0)

    # Likes
    likes: Mapped[List["Like"]] = relationship(
        primaryjoin="and_(Like.post_id == Post.id, Like.post_id.isnot(None))",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    # Comments
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="desc(Comment.created_at)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="posts")
    original_post: Mapped["Post"] = relationship("Post", remote_side=[id])

    # Group relation
    group: Mapped["Group"] = relationship("Group", back_populates="posts")

    def __repr__(self) -> str:
        return f"<Post {self.id} by User {self.user_id}>"

    def is_liked_by_user(self, user_id):
        return any(like.user_id == user_id for like in self.likes)

    def total_likes(self) -> int:
        return len(self.likes)

    def total_comments(self) -> int:
        return len(self.comments)

    def latest_comments(self, limit=3):
        return self.comments[:limit]


# Comment model
class Comment(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    post: Mapped["Post"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()

    likes: Mapped[List["Like"]] = relationship(
        primaryjoin="and_(Like.comment_id == Comment.id, Like.comment_id.isnot(None))",
        back_populates="comment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Comment {self.id} on Post {self.post_id}>"

    def is_liked_by_user(self, user_id):
        return any(like.user_id == user_id for like in self.likes)

    def total_likes(self) -> int:
        return len(self.likes)


# Like model
class Like(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post.id"), nullable=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comment.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    # One of post_id or comment_id must be filled
    __table_args__ = (
        db.CheckConstraint(
            "(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)",
            name="like_on_one_type",
        ),
    )

    # Relationship to post and comment
    post: Mapped["Post"] = relationship(back_populates="likes", foreign_keys=[post_id])
    comment: Mapped["Comment"] = relationship(
        back_populates="likes", foreign_keys=[comment_id]
    )

    user: Mapped["User"] = relationship(back_populates="likes")

    def __repr__(self) -> str:
        return f"<Like {self.id} by User {self.user_id}>"


# Message model
class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    sender: Mapped["User"] = relationship(
        foreign_keys=[sender_id], backref="sent_messages"
    )
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id], backref="received_messages"
    )

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id} to {self.recipient_id}>"

    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            "content": self.content,
            "sender_id": self.sender_id,
            "sender": {
                "image": self.sender.image,
                "name": self.sender.name,
                "surname": self.sender.surname,
            },
            "recipient_id": self.recipient_id,
            "created_at": format_message_time(self.created_at),
            "created_at_iso": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


# Notification Enum
class NotificationEnum(enum.Enum):
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    POST_LIKE = "post_like"
    POST_COMMENT = "post_comment"
    POST_SHARE = "post_share"
    COMMENT_LIKE = "comment_like"
    # Group notifications
    GROUP_INVITE="group_invite"
    INVITE_ACCEPTED="invite_accepted"
    ADMIN_PROMOTION="admin_promotion"


class Notification(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    notification_type: Mapped[NotificationEnum] = mapped_column(
        # Modified with ChatGPT because I was getting Enum keys instead of Enum values
        Enum(NotificationEnum, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    post_id: Mapped[int] = mapped_column(ForeignKey("post.id", ondelete="CASCADE"), nullable=True)
    comment_id: Mapped[int] = mapped_column(ForeignKey("comment.id", ondelete="CASCADE"), nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    # Relationships
    recipient: Mapped["User"] = relationship(
        foreign_keys=[recipient_id], backref="received_notifications"
    )
    sender: Mapped["User"] = relationship(foreign_keys=[sender_id])
    post: Mapped["Post"] = relationship()
    comment: Mapped["Comment"] = relationship()

    def __repr__(self):
        return f"<Notification {self.id} from {self.sender_id} to {self.recipient_id}>"

    def to_dict(self):
        """Convert notification to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "type": self.notification_type.value,
            "sender_name": f"{self.sender.name} {self.sender.surname}",
            "sender_username": self.sender.username,
            "sender_image": self.sender.image,
            "created_at": format_time_ago(self.created_at),
            "created_at_iso": self.created_at.isoformat(),
            "is_read": self.is_read,
            "post_id": self.post_id,
            "comment_id": self.comment_id,
        }


class GroupType(enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class GroupRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Group(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    image: Mapped[str] = mapped_column(String(300), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    about: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    group_type: Mapped[GroupType] = mapped_column(
        Enum(GroupType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="owned_groups")

    # Many-to-Many relationship for admins
    admins: Mapped[List["User"]] = relationship(
        secondary=group_admins,
        primaryjoin="Group.id == admins.c.group_id",
        secondaryjoin="User.id == admins.c.user_id",
        back_populates="admin_in",
        lazy="dynamic",
    )

    # Many-to-Many relationship for members
    members: Mapped[List["User"]] = relationship(
        secondary=group_members,
        primaryjoin="Group.id == members.c.group_id",
        secondaryjoin="User.id == members.c.user_id",
        back_populates="member_in",
        lazy="dynamic",
    )

    invitations: Mapped[List["Invitation"]] = relationship(
        back_populates="group", lazy=True, cascade="all, delete"
    )

    # Posts relationship
    posts: Mapped[List["Post"]] = relationship(
        back_populates="group",
        lazy="dynamic",
        cascade="all, delete",
        order_by="desc(Post.created_at)",
    )

    def __repr__(self):
        return f"<Group {self.id} by {self.owner_id}>"

    def can_post(self, user: User) -> bool:
        return user == self.owner or user in self.admins or user in self.members

    def total_posts(self) -> int:
        return len(self.posts)

    # Check if a user can remove another user or post from the group
    def can_remove_user(self, user: User, target_user: User) -> bool:
        if user == self.owner:
            return target_user != self.owner

        elif user in self.admins:
            return (
                target_user != self.owner
                and target_user not in self.admins
                and target_user in self.members
            )
            
        return False

    # Remove a user from the group
    def remove_user(self, user: User):
        if user in self.admins:
            self.admins.remove(user)
        if user in self.members:
            self.members.remove(user)

    def can_view(self, user: User) -> bool:
        return (
            self.group_type == GroupType.PUBLIC
            or user == self.owner
            or user in self.admins
            or user in self.members
        )

    def get_admins(self, limit=3):
        return self.admins[:limit]

    def get_members(self, limit=10):
        return self.members[:limit]

    def has_pending_invitation(self, user: User) -> bool:
        return any(invitation.invitee_id == user.id for invitation in self.invitations)

    def is_member(self, user: User) -> bool:
        return self.owner_id == user.id or user in self.admins or user in self.members


class Invitation(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=False)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    invitee_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    group: Mapped["Group"] = relationship(back_populates="invitations")
    inviter: Mapped["User"] = relationship(
        foreign_keys=[inviter_id], back_populates="sent_invitations"
    )
    invitee: Mapped["User"] = relationship(
        foreign_keys=[invitee_id], back_populates="received_invitations"
    )
