from app import db

def reset_db():
    """Drop all tables and recreate them."""
    db.drop_all()
    db.create_all()