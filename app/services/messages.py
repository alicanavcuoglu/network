from app.events import connected_users
from app.models import Message, db
from app.services import socketio


def create_message(sender_id, recipient_id, content):
    message = Message(recipient_id=recipient_id, sender_id=sender_id, content=content)

    db.session.add(message)

    return message


def emit_message(message):
    """Emit message to specific user"""
    recipient_sid = connected_users.get(message.recipient_id)
    if recipient_sid:
        socketio.emit("message", message.to_dict(), to=recipient_sid)
