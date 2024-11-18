from datetime import datetime, timedelta


# By ChatGPT
def format_time_ago(dt: datetime):
    now = datetime.utcnow()
    diff = now - dt

    # Display minutes ago if less than 1 hours
    if diff < timedelta(minutes=60):
        minutes = diff.seconds // 60
        return f"{minutes}m" if minutes > 1 else "just now"

    # Display hours ago if less than 24 hours
    elif diff < timedelta(hours=24):
        hours = diff.seconds // 3600
        return f"{hours}h"

    # Display days ago if within the last 7 days
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d"

    # Display as mm-dd-yyyy if older than 7 days
    else:
        return dt.strftime("%m-%d-%Y")


def format_message_time(dt: datetime):
    now = datetime.utcnow()
    diff = now - dt

    def plural(n: int, word: str):
        return f"{n} {word}{'s' if n != 1 else ''}"

    # Within last minute
    if diff < timedelta(minutes=1):
        return "Just now"

    # Within last hour
    if diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"{plural(minutes, 'minute')} ago"

    # Within last day
    if diff < timedelta(days=1):
        return dt.strftime('%-I:%M %p')

    # Yesterday
    if diff < timedelta(days=2):
        return f"Yesterday at {dt.strftime('%-I:%M %p')}"

    # Within last week
    if diff < timedelta(days=7):
        return f"{dt.strftime('%a')} at {dt.strftime('%-I:%M %p')}"

    # Within current year
    if dt.year == now.year:
        return f"{dt.strftime('%b %-d')} at {dt.strftime('%-I:%M %p')}"

    # Older dates
    return f"{dt.strftime('%b %-d, %Y')} at {dt.strftime('%-I:%M %p')}"