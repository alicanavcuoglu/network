from flask import request, session, url_for
from flask_socketio import emit

from app.utils.time_utils import format_time_ago
from app.models import db, Message, User

connected_users = {}


def init_socketio(socketio):
    @socketio.on("connect")
    def handle_connect():
        user_id = session.get("user_id")
        if user_id:
            connected_users[user_id] = request.sid

    @socketio.on("disconnect")
    def handle_disconnect():
        user_id = session.get("user_id")
        if user_id in connected_users:
            del connected_users[user_id]  # Remove SID when the user disconnects

    return socketio
