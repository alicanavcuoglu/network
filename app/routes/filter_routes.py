from markupsafe import Markup

from app.routes import filters_bp
from app.utils.helpers import (
    create_notification_link,
    create_notification_message,
    process_text,
)
from app.utils.time_utils import format_message_time, format_time_ago


@filters_bp.app_template_filter("time_ago")
def time_ago_filter(dt):
    return format_time_ago(dt)


@filters_bp.app_template_filter("message_time")
def message_time_filter(dt):
    return format_message_time(dt)


@filters_bp.app_template_filter("notification_message")
def notification_message_converter(notification):
    return create_notification_message(notification)


@filters_bp.app_template_filter("notification_link")
def notification_link_converter(notification):
    return create_notification_link(notification)


@filters_bp.app_template_filter("process_text")
def process_text_filter(text):
    processed = process_text(text)
    return Markup(processed)
