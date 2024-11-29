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

from app.extensions import db
from app.models import Group, Invitation, Post, User
from app.routes import group_bp
from app.services.queries import (
    get_group_admins,
    get_group_members,
    get_group_posts,
    get_groups,
    get_users_to_invite,
)
from app.utils.helpers import allowed_file, delete_file_from_s3, upload_file_to_s3


@group_bp.route("/groups")
def index():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q")

    # Get groups
    pagination = get_groups(page=page, search_query=search_query)

    return render_template(
        "groups/index.html",
        page=page,
        search_query=search_query,
        groups=pagination.items,
        pagination=pagination,
    )

    
@group_bp.route("/my-groups")
def my_groups():
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q")

    # Get groups
    pagination = get_groups(page=page, search_query=search_query, user_id=session["user_id"])

    return render_template(
        "groups/index.html",
        page=page,
        search_query=search_query,
        groups=pagination.items,
        pagination=pagination,
    )


@group_bp.route("/groups/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        image = request.files.get("image")
        name = request.form["name"]
        about = request.form["about"]
        privacy = request.form["privacy"]

        # TODO: Add group rules

        # Check required fields exists
        if not name or not about or not privacy:
            flash("Please fill the required fields!", "error")
            return redirect(url_for("group.create"))

        image_key = upload_file_to_s3(image, folder="group-image")

        group = Group(
            owner_id=session["user_id"],
            image=image_key,
            name=name,
            about=about,
            group_type=privacy,
        )

        # Save changes
        try:
            db.session.add(group)
            db.session.commit()
            flash("Successfully created a group.", "success")
            return redirect(url_for("group.page", id=group.id))
        except:
            db.session.rollback()
            flash("Something went wrong, try again.", "error")
            return redirect(url_for("group.create"))

    return render_template("groups/create.html")


@group_bp.route("/groups/<id>", methods=["GET", "POST"])
def page(id):
    group = db.get_or_404(Group, id)

    if request.method == "POST":
        current_user = db.get_or_404(User, session["user_id"])
        if not group.can_post(current_user):
            flash("You don't have permission to post in this group", "error")
            return redirect(url_for("group.page", id=id))

        content = request.form["content"]
        post = Post(content=content, user_id=session["user_id"], group_id=group.id)
        db.session.add(post)
        db.session.commit()

    page = request.args.get("page", 1, type=int)
    pagination = get_group_posts(group_id=group.id, page=page)

    return render_template(
        "groups/group/index.html",
        posts=pagination.items,
        group=group,
        page=page,
        pagination=pagination,
    )


@group_bp.route("/groups/<id>/invite", methods=["GET", "POST"])
def invite(id):
    group = db.get_or_404(Group, id)

    if request.method == "POST":
        user_id = request.json

        if not user_id:
            flash("User ID is required")
            return jsonify({"error": "User ID required"}), 400

        user = db.get_or_404(User, user_id)

        if user in group.members or user in group.admins or user == group.owner:
            return jsonify({"error": "User already in group"}), 400
        
        existing_invitation = Invitation.query.filter_by(
            group_id=group.id,
            invitee_id=user.id,
            inviter_id=session["user_id"]
        ).first()

        if existing_invitation:
            return jsonify({"error": "Invitation already sent"}), 400

        invitation = Invitation(
            group_id=group.id, invitee_id=user.id, inviter_id=session["user_id"]
        )

        db.session.add(invitation)

        # TODO: Add notification
        db.session.commit()
        
        return "success", 200

    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q")
    pagination = get_users_to_invite(
        page=page, search_query=search_query, group_id=group.id
    )

    return render_template(
        "groups/group/invite.html",
        users=pagination.items,
        group=group,
        page=page,
        pagination=pagination,
        search_query=search_query,
    )


@group_bp.route("/groups/<id>/about")
def about(id):
    group = db.get_or_404(Group, id)

    return render_template("groups/group/about.html", posts=group.posts, group=group)


@group_bp.route("/groups/<id>/members")
def members(id):
    group = db.get_or_404(Group, id)

    return render_template("groups/group/members.html", group=group)


@group_bp.route("/groups/<id>/members/admins")
def all_admins(id):
    group = db.get_or_404(Group, id)
    page = request.args.get("page", 1, type=int)
    pagination = get_group_admins(group_id=group.id, page=page)

    return render_template(
        "groups/group/all_admins.html",
        admins=pagination.items,
        group=group,
        page=page,
        pagination=pagination,
    )


@group_bp.route("/groups/<id>/members/all")
def all_members(id):
    group = db.get_or_404(Group, id)
    page = request.args.get("page", 1, type=int)
    pagination = get_group_members(group_id=group.id, page=page)

    return render_template(
        "groups/group/all_members.html",
        members=pagination.items,
        group=group,
        page=page,
        pagination=pagination,
    )


@group_bp.route("/groups/<id>/settings", methods=["GET", "POST"])
def settings(id):
    group = db.get_or_404(Group, id)

    if session["user_id"] != group.owner_id:
        flash("Only group owner can access settings", "error")
        return redirect(url_for("group_bp.page", id=group.id))

    if request.method == "POST":

        image = request.files.get("image")
        name = request.form["name"]
        about = request.form["about"]
        privacy = request.form["privacy"]
        delete_image = True if request.form["delete_image"] == "true" else False

        if not name or not about or not privacy:
            flash("Please fill the required fields!", "error")
            return redirect(url_for("group.create"))

        group.name = name
        group.about = about
        group.group_type = privacy

        if image.filename:
            if not allowed_file(image.filename):
                return abort(422)

            delete_file_from_s3(group.image)
            image_key = upload_file_to_s3(image, folder="group-image")
            group.image = image_key

        elif group.image and delete_image and not image.filename:
            delete_file_from_s3(group.image)
            group.image = None

        # Save changes
        try:
            db.session.commit()
            flash("Successfully updated the group.", "success")
        except:
            db.session.rollback()
            flash("Something went wrong, try again.", "error")

        return redirect(url_for("group.settings", id=id))

    return render_template("groups/group/settings.html", group=group)


@group_bp.route("/groups/<id>/settings/admins", methods=["GET", "POST"])
def settings_admins(id):
    group = db.get_or_404(Group, id)
    page = request.args.get("page", 1, type=int)
    pagination = get_group_admins(group_id=id, page=page)

    return render_template(
        "groups/group/all_admins.html",
        admins=pagination.items,
        group=group,
        page=page,
        pagination=pagination,
    )


@group_bp.route("/groups/<id>/settings/delete", methods=["POST"])
def delete_group(id):
    group = Group.query.filter(
        Group.id == id, Group.owner_id == session["user_id"]
    ).first_or_404()

    db.session.delete(group)
    db.session.commit()

    flash(f"Group {group.name} deleted successfully.", "success")
    return redirect(url_for("main.feed"))


# @group_bp.route("/groups/<id>/rules")
# def rules(id):
#     group = Group.query.get_or_404(id)
#     return group.rules, 200


@group_bp.route("/groups/<id>/posts/<post_id>")
def post(id, post_id):
    group = db.get_or_404(Group, id)
    post = Post.query.filter(Post.id == post_id, Post.group_id == id).first_or_404()

    return render_template("groups/group/post_page.html", group=group, post=post)


@group_bp.route("/groups/<id>/join", methods=["POST"])
def join_group(id):
    user = db.get_or_404(User, session["user_id"])
    group = db.get_or_404(Group, id)

    group.members.append(user)

    db.session.commit()

    flash(f"You have joined {group.name}!", "success")
    return "success", 200


@group_bp.route("/groups/<id>/invite/accept", methods=["POST"])
def accept_invite(id):
    user = db.get_or_404(User, session["user_id"])
    group = db.get_or_404(Group, id)

    invitation = Invitation.query.filter_by(
        group_id=group.id,
        invitee_id=user.id,
    ).first_or_404()

    group.members.append(user)
    db.session.delete(invitation)
    
    # TODO: Send notification to inviter

    db.session.commit()

    flash(f"You have joined {group.name}!", "success")
    return "success", 200


@group_bp.route("/groups/<id>/invite/decline", methods=["POST"])
def decline_invite(id):
    user = db.get_or_404(User, session["user_id"])
    group = db.get_or_404(Group, id)

    invitation = Invitation.query.filter_by(
        group_id=group.id,
        invitee_id=user.id,
    ).first_or_404()

    db.session.delete(invitation)

    db.session.commit()

    flash(f"You declined invitation from {group.name}!", "success")
    return "success", 200


@group_bp.route("/groups/<id>/leave", methods=["POST"])
def leave(id):
    current_user = db.get_or_404(User, session["user_id"])

    group = db.get_or_404(Group, id)

    group.remove_user(current_user)
    db.session.commit()

    flash(f"You left {group.name}!", "success")
    return redirect(url_for("group.page", id=id))


@group_bp.route("/groups/<id>/remove-user/<user_id>", methods=["POST"])
def remove_user(id, user_id):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = db.get_or_404(User, user_id)
    group = db.get_or_404(Group, id)

    if not group.can_remove_user(current_user, target_user):
        flash("You don't have permission to remove this user", "error")
        return "unauthorized", 401

    # Remove from appropriate list
    if target_user in group.admins:
        group.admins.remove(target_user)
    if target_user in group.members:
        group.members.remove(target_user)

    db.session.commit()

    flash(f"Removed {target_user.name} {target_user.surname} from the group", "success")
    return "success", 200


@group_bp.route("/groups/<id>/make-admin/<user_id>", methods=["POST"])
def make_admin(id, user_id):
    current_user = db.get_or_404(User, session["user_id"])
    target_user = db.get_or_404(User, user_id)
    group = db.get_or_404(Group, id)

    if current_user.id != group.owner_id:
        flash("Only owner or admins can remove a user from the group", "error")
        return "unauthorized", 401

    if target_user not in group.members:
        flash("User must be a member to be made admin", "error")
        return "not found", 404

    if target_user in group.admins:
        flash("User is already an admin", "error")
        return "bad request", 400

   # Move from member to admin
    group.members.remove(target_user)
    group.admins.append(target_user)
    db.session.commit()

    # TODO: Send notification to new admin
    # You're now admin in {group.name}!

    flash(f"{target_user.name} {target_user.surname} is now an admin", "success")
    return "success", 200

@group_bp.route("/groups/<id>/revoke-admin/<user_id>", methods=["POST"])
def revoke_admin(id, user_id):
   current_user = db.get_or_404(User, session["user_id"])
   target_user = db.get_or_404(User, user_id)
   group = db.get_or_404(Group, id)

   if current_user.id != group.owner_id:
       flash("Only the owner can revoke admin privileges", "error")
       return "unauthorized", 401

   if target_user not in group.admins:
       flash("User is not an admin", "error")
       return "bad request", 400

   # Move from admin to member
   group.admins.remove(target_user)
   group.members.append(target_user)
   db.session.commit()

   flash(f"Revoked admin privileges from {target_user.name} {target_user.surname}", "success")
   return "success", 200