from flask import (
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import (
    Comment,
    Like,
    Message,
    Notification,
    NotificationEnum,
    Post,
    User,
)
from app.routes import main_bp
from app.routes.error_routes import unauthorized
from app.services.messages import create_message, emit_message
from app.services.notifications import (
    create_notification,
    emit_notification,
    get_all_unread_notifications,
    get_next_notification,
    get_notifications,
    get_unread_notifications,
    mark_as_read,
)
from app.services.queries import (
    get_community_posts,
    get_friends,
    get_latest_conversations,
    get_posts,
    get_requests,
    get_user_by_username,
    get_user_posts,
    get_users,
    get_users_groups,
)
from app.utils.helpers import (
    allowed_file,
    array_to_str,
    delete_file_from_s3,
    upload_file_to_s3,
)
from app.utils.time_utils import format_time_ago


@main_bp.route("/profiles")
def user_list():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q")

    # Get users
    users = get_users(search_query=search_query, page=page)

    return render_template(
        "users/profiles.html",
        users=users.items,
        page=page,
        search_query=search_query,
        pagination=users,
    )


# User's posts
@main_bp.route("/profiles/<username>")
def user_profile(username):
    page = request.args.get("page", 1, type=int)
    user = get_user_by_username(username, posts=True)
    is_friends = user.is_friends(session["user_id"])

    # If user is neither friend nor have a public account don't display posts
    if user.is_private and not is_friends and user.id != session["user_id"]:
        return render_template(
            "users/profile/index.html", user=user, posts=[], can_view=False
        )

    pagination = get_user_posts(user_id=user.id, page=page)

    return render_template(
        "users/profile/index.html",
        user=user,
        posts=pagination.items,
        can_view=True,
        page=page,
        pagination=pagination,
    )


# User's about
@main_bp.route("/profiles/<username>/about")
def user_profile_about(username):
    user = get_user_by_username(username)

    return render_template("users/profile/about.html", user=user)


# User's friends
@main_bp.route("/profiles/<username>/friends")
def user_profile_friends(username):
    user = get_user_by_username(username)
    is_friends = user.is_friends(session["user_id"])

    if user.is_private and not is_friends and user.id != session["user_id"]:
        return render_template(
            "users/profile/friends.html", user=user, friends=[], can_view=False
        )

    page = request.args.get("page", 1, type=int)

    # Get friends
    friends = get_friends(user.id, page=page)

    return render_template(
        "users/profile/friends.html",
        user=user,
        friends=friends.items,
        can_view=True,
        page=page,
        pagination=friends,
    )


# User's groups
@main_bp.route("/profiles/<username>/groups")
def user_profile_groups(username):
    user = db.first_or_404(db.select(User).filter_by(username=username))
    is_friends = user.is_friends(session["user_id"])

    if user.is_private and not is_friends and user.id != session["user_id"]:
        return render_template(
            "users/profile/groups.html", user=user, groups=[], can_view=False
        )

    page = request.args.get("page", 1, type=int)

    # Get user's groups
    groups = get_users_groups(user_id=user.id, page=page)

    return render_template(
        "users/profile/groups.html",
        user=user,
        groups=groups.items,
        can_view=True,
        page=page,
        pagination=groups,
    )


""" SETTINGS """


@main_bp.route("/settings")
def settings():
    user = db.get_or_404(User, session["user_id"])

    return render_template("users/settings.html", user=user)


@main_bp.route("/profiles/<int:id>/delete", methods=["POST"])
def user_delete(id):
    user = db.get_or_404(User, id)

    if user.id != session["user_id"]:
        return abort(401)

    delete_file_from_s3(user.image)

    db.session.delete(user)
    db.session.commit()
    session.clear()
    return redirect(url_for("main.feed"))


@main_bp.route("/settings/general", methods=["POST"])
def general_settings():
    image = request.files["image"]
    name = request.form["name"]
    surname = request.form["surname"]
    email = request.form["email"]
    is_private = request.form.get("is_private")
    delete_image = True if request.form["delete_image"] == "true" else False

    # Get user
    current_user = db.get_or_404(User, session["user_id"])

    # If email exists don't change
    if email and email != current_user.email:
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(
                "This email is already in use. Please use a different email.", "error"
            )
            return redirect(url_for("main.settings"))
        current_user.email = email

    if name and name != current_user.name:
        current_user.name = name
    if surname and surname != current_user.surname:
        current_user.surname = surname
    if email and email != current_user.email:
        current_user.email = email

    # Set user's account private / public
    if is_private:
        current_user.is_private = True
    else:
        current_user.is_private = False

    if image.filename:
        if not allowed_file(image.filename):
            return abort(422)

        delete_file_from_s3(current_user.image)
        image_key = upload_file_to_s3(image)
        current_user.image = image_key

    elif current_user.image and delete_image and not image.filename:
        delete_file_from_s3(current_user.image)
        current_user.image = None

    # Save changes
    try:
        db.session.commit()
        flash("Your profile has been updated successfully!", "success")
    except:
        db.session.rollback()
        flash("Something went wrong, try again.", "error")

    return redirect(url_for("main.settings"))


@main_bp.route("/settings/password", methods=["POST"])
def password_settings():
    current_password = request.form["current-password"]
    new_password = request.form["new-password"]
    new_password_again = request.form["new-password-again"]

    # Get user
    user = db.get_or_404(User, session["user_id"])

    # Check if the current password is correct
    if not check_password_hash(user.password, current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("main.settings"))

    # Check if the new passwords match
    if new_password != new_password_again:
        flash("New passwords do not match.", "error")
        return redirect(url_for("main.settings"))

    # Check password for minimum length
    if len(new_password) < 8:
        flash("New password must be at least 8 characters long.", "error")
        return redirect(url_for("main.settings"))

    # Update the user's password
    user.password = generate_password_hash(new_password)
    db.session.commit()

    flash("Your password has been changed successfully!", "success")
    return redirect(url_for("main.settings"))


@main_bp.route("/settings/info", methods=["POST"])
def info_settings():
    # Get user
    user = db.get_or_404(User, session["user_id"])

    # Get form data
    location = request.form.get("location")
    about_me = request.form.get("about-me")
    working_on = request.form.get("working-on")
    interests = request.form.getlist("interests[]")

    # Convert array to string
    interests_string = array_to_str(interests)

    # Update user fields if they have changed
    if location != user.location:
        user.location = location

    if about_me != user.about:
        user.about = about_me

    if working_on != user.working_on:
        user.working_on = working_on

    # Update interests if changed
    if interests_string != user.interests:
        user.interests = interests_string

    # Commit the changes to the database
    db.session.commit()

    # Flash success message and redirect
    flash("Your information has been updated successfully.", "success")
    return redirect(url_for("main.settings"))


@main_bp.route("/settings/classes", methods=["POST"])
def classes_settings():
    selected_classes = request.form.getlist("classes[]")

    classes_string = array_to_str(selected_classes)

    # Get the user
    user = db.get_or_404(User, session["user_id"])

    # Update the user's classes field with the new values
    user.classes = classes_string

    # Save changes to the database
    db.session.commit()

    # Flash a success message and redirect to the settings page
    flash("Your classes have been updated successfully!", "success")
    return redirect(url_for("main.settings"))


@main_bp.route("/settings/links", methods=["POST"])
def links_settings():
    links = request.form.getlist("link[]")

    links_string = array_to_str(links)

    # Get the user
    user = db.get_or_404(User, session["user_id"])

    # Update the user's links
    user.links = links_string

    # Save changes to the database
    db.session.commit()

    # Flash a success message and redirect to the settings page
    flash("Your links have been updated successfully!", "success")
    return redirect(url_for("main.settings"))


""" POSTS """


# Feed
@main_bp.route("/")
def feed():
    current_user = db.get_or_404(User, session["user_id"])
    page = request.args.get("page", 1, type=int)

    pagination = get_community_posts(
        user_id=current_user.id,
        friends=current_user.friends,
        page=page,
    )

    return render_template(
        "feed.html", posts=pagination.items, page=page, pagination=pagination
    )


# Friends feed
@main_bp.route("/my-feed")
def my_feed():
    current_user = db.get_or_404(User, session["user_id"])
    page = request.args.get("page", 1, type=int)

    pagination = get_posts(
        user_id=current_user.id,
        friends=current_user.friends,
        page=page,
    )

    return render_template(
        "my_feed.html", posts=pagination.items, page=page, pagination=pagination
    )


# Post page
@main_bp.route("/posts/<int:id>")
def post_page(id):
    post = Post.query.get_or_404(id)
    return render_template("post_page.html", post=post)


# Create post
@main_bp.route("/post", methods=["POST"])
def create_post():
    content = request.form["content"]
    post = Post(content=content, user_id=session["user_id"])
    db.session.add(post)
    db.session.commit()
    return redirect(url_for("main.feed"))


# Reshare post
@main_bp.route("/post/<id>/reshare", methods=["POST"])
def reshare_post(id):
    current_user = db.get_or_404(User, session["user_id"])
    parent_post = Post.query.get_or_404(id)
    parent_post.shares += 1
    content = request.form["content"]

    post = Post(content=content, parent_id=parent_post.id, user_id=session["user_id"])
    db.session.add(post)
    db.session.flush()

    # Create a notification for original_post user
    if current_user.id != parent_post.user_id:
        notification = create_notification(
            recipient_id=parent_post.user_id,
            post_id=post.id,
            sender_id=session["user_id"],
            notification_type=NotificationEnum.POST_SHARE,
        )

    db.session.commit()

    # Emitting notification before commit creates error, took me an hour to debug
    if current_user.id != parent_post.user_id:
        # Emit notification with SocketIO
        emit_notification(notification)

    return redirect(url_for("main.feed"))


# Delete post
@main_bp.route("/post/delete/<id>", methods=["DELETE"])
def delete_post(id):
    current_user = db.get_or_404(User, session["user_id"])
    post = db.get_or_404(Post, id)

    if not post:
        flash("Can't delete the post!", "error")
        return "bad request!", 400

    if post.user_id == current_user.id:
        can_delete = True
    elif post.group:
        can_delete = post.group.can_remove_user(current_user, post.user)

    if not can_delete:
        flash("You don't have permission to delete this post.", "error")
        return unauthorized()

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully.", "success")

    return jsonify({"success": True})


# Like post
@main_bp.route("/like/<id>", methods=["POST"])
def like_post(id):
    current_user = db.get_or_404(User, session["user_id"])
    post = db.get_or_404(Post, id)

    # Convert liked posts to array
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    # Check if the post is already liked by the user
    if like:
        # Unlike the post if already liked
        db.session.delete(like)
        is_liked = False
    else:
        # Like the post
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        is_liked = True

    if current_user.id != post.user_id and not like:
        notification = create_notification(
            recipient_id=post.user_id,
            post_id=post.id,
            sender_id=current_user.id,
            notification_type=NotificationEnum.POST_LIKE,
        )

    # Update the user's liked posts and the post's like count, also create notification
    db.session.commit()

    if current_user.id != post.user_id and not like:
        # Emit notification with SocketIO
        emit_notification(notification)

    like_count = len(post.likes)

    return jsonify({"likes": like_count, "isLiked": is_liked})


# Like comment
@main_bp.route("/like/comment/<id>", methods=["POST"])
def like_comment(id):
    current_user = db.get_or_404(User, session["user_id"])
    comment = db.get_or_404(Comment, id)

    # Liked comments
    like = Like.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()

    # Check if the comment is already liked by the user
    if like:
        # Unlike the comment if already liked
        db.session.delete(like)
        is_liked = False
    else:
        # Like the comment
        new_like = Like(user_id=current_user.id, comment_id=comment.id)
        db.session.add(new_like)
        is_liked = True

    # Create a notification for comment's user
    if current_user.id != comment.user_id:
        notification = create_notification(
            recipient_id=comment.user_id,
            sender_id=current_user.id,
            comment_id=comment.id,
            post_id=comment.post_id,
            notification_type=NotificationEnum.COMMENT_LIKE,
        )

    # Update the user's liked posts and the post's like count
    db.session.commit()

    if current_user.id != comment.user_id:
        # Emit notification with SocketIO
        emit_notification(notification)

    like_count = len(comment.likes)

    return jsonify({"likes": like_count, "isLiked": is_liked})


@main_bp.route("/comment/<id>", methods=["POST"])
def comment_post(id):
    content = request.json

    current_user = db.get_or_404(User, session["user_id"])
    post = db.get_or_404(Post, id)

    # Create comment
    comment = Comment(user_id=current_user.id, post_id=post.id, content=content)
    db.session.add(comment)
    db.session.flush()

    # Create a notification for post user
    if current_user.id != post.user_id:
        notification = create_notification(
            recipient_id=post.user_id,
            sender_id=current_user.id,
            comment_id=comment.id,
            post_id=post.id,
            notification_type=NotificationEnum.POST_COMMENT,
        )

    db.session.commit()

    if current_user.id != post.user_id:
        # Emit notification with SocketIO
        emit_notification(notification)

    comment_data = {
        "id": comment.id,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "content": comment.content,
        "timestamp": comment.created_at,
    }

    return jsonify({"comment": comment_data})


# Delete comment
@main_bp.route("/comment/delete/<id>", methods=["DELETE"])
def delete_comment(id):
    current_user = db.get_or_404(User, session["user_id"])
    comment = db.get_or_404(Comment, id)

    if not comment:
        flash("Can't delete the comment!", "error")
        return "bad request!", 400

    if comment.user_id == current_user.id:
        can_delete = True
    elif comment.post.group:
        can_delete = comment.post.group.can_remove_user(current_user, comment.user)

    if not can_delete:
        flash("You don't have permission to delete this comment.", "error")
        return unauthorized()

    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted successfully.", "success")

    return jsonify({"success": True})


# Load more comments
@main_bp.route("/post/<id>/comments")
def load_more_comments(id):
    page = int(request.args["page"]) + 1
    comments = (
        Comment.query.filter_by(post_id=id)
        .order_by(Comment.created_at.asc())
        .paginate(page=page, per_page=3)
    )
    comment_list = []

    for comment in comments:
        # Append json data
        comment_data = {
            "id": comment.id,
            "post_id": comment.post_id,
            "user": {
                "username": comment.user.username,
                "name": comment.user.name,
                "surname": comment.user.surname,
                "image": comment.user.image,
            },
            "content": comment.content,
            "created_at_iso": comment.created_at,
            "created_at": format_time_ago(comment.created_at),
            "own_post": comment.user_id == session["user_id"],
            "is_liked_by_user": comment.is_liked_by_user(session["user_id"]),
            "total_likes": comment.total_likes(),
        }
        comment_list.append(comment_data)

    return jsonify({"comments": comment_list, "has_next": comments.has_next})


""" FRIENDS """


@main_bp.route("/friends")
def friends():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q")
    users = get_users(
        search_query=search_query,
        page=page,
        get_friends=True,
        user_id=session["user_id"],
    )

    return render_template(
        "users/profiles.html",
        users=users.items,
        page=page,
        search_query=search_query,
        pagination=users,
        show_requests=True,
    )


# Requests
@main_bp.route("/friends/requests")
def friend_requests():
    user = db.get_or_404(User, session["user_id"])

    received_requests = get_requests(user.id)

    return render_template("users/requests.html", users=received_requests)


# Send a friend request
@main_bp.route("/requests/<username>", methods=["POST"])
def send_friend_request(username):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        flash("User not found!", "error")
        return "", 200

    if target_user in current_user.friends:
        flash("You're already friends with this user.", "info")
        return "", 200

    elif target_user in current_user.pending_requests:
        flash("Friend request already sent.", "info")
        return "", 200

    # Accept the request if current user was already requested by the target user
    elif current_user in target_user.pending_requests:
        current_user.friends.append(target_user)
        target_user.friends.append(current_user)

        # Remove pending/received requests
        current_user.received_requests.remove(target_user)
        target_user.pending_requests.remove(current_user)

        # Send a friend accept notification to target user
        notification = create_notification(
            recipient_id=target_user.id,
            sender_id=current_user.id,
            notification_type=NotificationEnum.FRIEND_ACCEPTED,
        )

        # Emit notification with SocketIO
        emit_notification(notification)

        # Update friend request notification to read if not read yet
        unread_request = Notification.query.filter(
            Notification.recipient_id == current_user.id,
            Notification.sender_id == target_user.id,
            Notification.notification_type == NotificationEnum.FRIEND_REQUEST.value,
            Notification.is_read == False,
        ).first()

        if unread_request:
            unread_request.is_read = True

        db.session.commit()

        flash(
            f"You are now friends with {target_user.name} {target_user.surname}.",
            "success",
        )
        return "", 200

    current_user.pending_requests.append(target_user)
    target_user.received_requests.append(current_user)

    # Send a friend request notification to target user
    notification = create_notification(
        recipient_id=target_user.id,
        sender_id=current_user.id,
        notification_type=NotificationEnum.FRIEND_REQUEST,
    )

    db.session.commit()

    # Emit notification with SocketIO
    emit_notification(notification)

    flash(
        f"Friend request sent to {target_user.name} {target_user.surname}.", "success"
    )
    return jsonify({"username": target_user.username, "status": "success"})


# Accept a friend request
@main_bp.route("/requests/<username>/accept", methods=["POST"])
def accept_friend_request(username):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = User.query.filter_by(username=username).one_or_404()

    if target_user in current_user.friends:
        flash("You're already friends with this user.", "info")
        return "", 200

    # Accept the request if current user was already requested by the target user
    current_user.friends.append(target_user)
    target_user.friends.append(current_user)

    # Remove pending/received requests
    current_user.received_requests.remove(target_user)
    target_user.pending_requests.remove(current_user)
    # Send a notification
    notification = create_notification(
        recipient_id=target_user.id,
        sender_id=current_user.id,
        notification_type=NotificationEnum.FRIEND_ACCEPTED,
    )
    # Before emitting
    db.session.flush()

    # Emit notification with SocketIO
    emit_notification(notification)

    # Update friend request notification to read if not read yet
    unread_request = Notification.query.filter(
        Notification.recipient_id == current_user.id,
        Notification.sender_id == target_user.id,
        Notification.notification_type == NotificationEnum.FRIEND_REQUEST.value,
        Notification.is_read == False,
    ).first()

    if unread_request:
        unread_request.is_read = True

    db.session.commit()

    flash(
        f"You're now friends with {target_user.name} {target_user.surname}.", "success"
    )
    return jsonify({"username": target_user.username, "status": "success"})


# Decline a friend request
@main_bp.route("/requests/<username>/decline", methods=["POST"])
def decline_friend_request(username):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = User.query.filter_by(username=username).one_or_404()

    if target_user in current_user.friends:
        flash("You're already friends with this user.", "info")
        return "", 200

    # Remove pending/received requests
    current_user.received_requests.remove(target_user)
    target_user.pending_requests.remove(current_user)

    db.session.commit()

    flash(
        f"Friend request from {target_user.name} {target_user.surname} declined.",
        "success",
    )
    return jsonify({"username": target_user.username, "status": "success"})


# Remove a user from friends
@main_bp.route("/friends/<username>/remove", methods=["DELETE"])
def remove_friend(username):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = User.query.filter_by(username=username).one_or_404()

    if target_user not in current_user.friends:
        flash("You're not friends with this user.", "info")
        return "", 200

    # Remove pending/received requests
    current_user.friends.remove(target_user)
    target_user.friends.remove(current_user)

    db.session.commit()

    flash(f"{target_user.name} {target_user.surname} removed from friends.", "success")
    return jsonify({"username": target_user.username, "status": "success"})


""" MESSAGES """


# Messages page
@main_bp.route("/messages")
def view_messages():
    current_user = db.get_or_404(User, session["user_id"])
    messages = get_latest_conversations(current_user.id)

    return render_template("messages/index.html", messages=messages)


# Single message page
@main_bp.route("/messages/<username>", methods=["GET", "POST"])
def conversation(username):
    # Get current user and friend
    current_user = db.get_or_404(User, session["user_id"])
    friend = User.query.filter_by(username=username).first_or_404()

    if current_user.username == username:
        flash("You can't chat with yourself!", "error")
        return redirect(url_for("main.view_messages"))

    if request.method == "POST":
        # Get message from JS fetch request
        content = request.json

        # Create message
        message = create_message(
            sender_id=current_user.id, recipient_id=friend.id, content=content
        )

        # Commit
        db.session.commit()

        # Emit message
        emit_message(message)

        return message.to_dict(), 200

    else:
        # Limit the initial number of messages to load, for example, the latest 20
        message_limit = 20

        # Fetch initial messages between current user and friend
        messages = (
            Message.query.filter(
                (
                    (Message.sender_id == current_user.id)
                    & (Message.recipient_id == friend.id)
                )
                | (
                    (Message.sender_id == friend.id)
                    & (Message.recipient_id == current_user.id)
                )
            )
            .order_by(Message.created_at.desc())
            .limit(message_limit)
            .all()
        )

        # Reverse to show from oldest to newest after limiting
        messages.reverse()

        return render_template(
            "messages/conversation.html",
            messages=messages,
            friend=friend,
            has_more=len(messages) == message_limit,
        )


# Load more messages
@main_bp.route("/messages/<username>/more")
def load_more_conversation(username):
    # Get current user and friend
    current_user = db.get_or_404(User, session["user_id"])
    friend = User.query.filter_by(username=username).first_or_404()

    if current_user.username == username:
        flash("You can't chat with yourself!", "error")
        return redirect(url_for("main.view_messages"))

    # Limit the initial number of messages to load
    message_limit = 20
    page = int(request.args["page"]) + 1

    # Fetch initial messages between current user and friend
    messages = (
        Message.query.filter(
            (
                (Message.sender_id == current_user.id)
                & (Message.recipient_id == friend.id)
            )
            | (
                (Message.sender_id == friend.id)
                & (Message.recipient_id == current_user.id)
            )
        )
        .order_by(Message.created_at.desc())
        .paginate(page=page, per_page=message_limit)
    )

    message_list = []

    for message in messages:
        message_data = {
            "content": message.content,
            "sender": {
                "id": message.sender.id,
                "image": message.sender.image,
                "name": message.sender.name,
                "surname": message.sender.surname,
            },
            "sender_id": message.sender.id,
            "recipient_id": message.recipient_id,
            "created_at_iso": message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": format_time_ago(message.created_at),
        }
        message_list.append(message_data)

    return jsonify({"messages": message_list, "has_next": messages.has_next})


# Update read status
@main_bp.route("/messages/<username>/mark_read", methods=["POST"])
def mark_messages_as_read(username):
    # Get current user and friend
    current_user = db.get_or_404(User, session["user_id"])
    friend = User.query.filter_by(username=username).first_or_404()

    if current_user.username == username:
        flash("You can't chat with yourself!", "error")
        return redirect(url_for("main.view_messages"))

    unread_messages = Message.query.filter(
        Message.sender_id == friend.id,
        Message.recipient_id == current_user.id,
        Message.is_read == False,
    )

    for message in unread_messages:
        message.is_read = True

    other_unread_messages = Message.query.filter(
        Message.recipient_id == current_user.id, Message.is_read == False
    ).count()

    db.session.commit()
    return jsonify(
        {"success": True, "other_unread_messages": other_unread_messages > 0}
    )


@main_bp.route("/notifications")
def notifications():
    page = request.args.get("page", 1, type=int)

    pagination = get_notifications(session["user_id"], page=page)

    return render_template(
        "notifications.html",
        notifications=pagination.items,
        pagination=pagination,
        page=page,
    )


@main_bp.route("/notifications/unread/all")
def all_unread_notifications():
    page = request.args.get("page", 1, type=int)

    pagination = get_all_unread_notifications(session["user_id"], page=page)

    return render_template(
        "notifications_unread.html",
        notifications=pagination.items,
        pagination=pagination,
        page=page,
    )


@main_bp.route("/notifications/unread")
def unread_notifications():
    current_user = db.get_or_404(User, session["user_id"])
    notifications = get_unread_notifications(current_user.id)
    return jsonify([n.to_dict() for n in notifications])


@main_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id):
    notification = mark_as_read(notification_id, session["user_id"])

    if not notification:
        flash("Notification not found!", "error")
        return jsonify({"status": "error", "message": "Notification not found"}), 404

    return jsonify({"status": "success"})


@main_bp.route("/notifications/next-unread-notification", methods=["POST"])
def next_unread_notification():
    notifications = request.get_json()

    next_notification = get_next_notification(session["user_id"], notifications)

    if not next_notification:
        return jsonify({"has_more": False}), 204

    notification = next_notification.to_dict()

    return jsonify(notification)


@main_bp.route("/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    current_user = db.get_or_404(User, session["user_id"])
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update(
        {Notification.is_read: True}
    )
    db.session.commit()
    return jsonify({"status": "success"})


# Hashtag page
@main_bp.route("/tags")
def tag_view():
    page = request.args.get("page", 1, type=int)
    tag = request.args.get("tag")

    if not tag:
        return redirect(url_for("main.feed"))

    current_user = db.get_or_404(User, session["user_id"])

    pattern = f"%#{tag}%"

    pagination = get_community_posts(
        user_id=current_user.id,
        friends=current_user.friends,
        page=page,
        tag_pattern=pattern,
    )

    return render_template(
        "tags.html", posts=pagination.items, tag=tag, page=page, pagination=pagination
    )
