"""renamed is_public to is_private

Revision ID: b1f0694a078b
Revises: 4cd736581e96
Create Date: 2024-11-15 ...

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'b1f0694a078b'
down_revision = '4cd736581e96'
branch_labels = None
depends_on = None

def upgrade():
    # Create a temporary table with the new schema
    op.execute('''
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64),
            email VARCHAR(120),
            password VARCHAR(128),
            name VARCHAR(64),
            surname VARCHAR(64),
            about TEXT,
            working_on TEXT,
            classes TEXT,
            links TEXT,
            location TEXT,
            interests TEXT,
            image VARCHAR(120),
            is_completed BOOLEAN,
            is_private BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Copy the data, inverting is_public to is_private
    op.execute('''
        INSERT INTO user_new (
            id, username, email, password, name, surname, 
            about, working_on, classes, links, location, 
            interests, image, is_completed, is_private
        )
        SELECT 
            id, username, email, password, name, surname,
            about, working_on, classes, links, location,
            interests, image, is_completed, NOT is_public
        FROM user
    ''')
    
    # Drop the old table
    op.execute('DROP TABLE user')
    
    # Rename the new table to the original name
    op.execute('ALTER TABLE user_new RENAME TO user')

def downgrade():
    # Create a temporary table with the old schema
    op.execute('''
        CREATE TABLE user_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64),
            email VARCHAR(120),
            password VARCHAR(128),
            name VARCHAR(64),
            surname VARCHAR(64),
            about TEXT,
            working_on TEXT,
            classes TEXT,
            links TEXT,
            location TEXT,
            interests TEXT,
            image VARCHAR(120),
            is_completed BOOLEAN,
            is_public BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    
    # Copy the data back, inverting is_private to is_public
    op.execute('''
        INSERT INTO user_new (
            id, username, email, password, name, surname,
            about, working_on, classes, links, location,
            interests, image, is_completed, is_public
        )
        SELECT 
            id, username, email, password, name, surname,
            about, working_on, classes, links, location,
            interests, image, is_completed, NOT is_private
        FROM user
    ''')
    
    # Drop the new table
    op.execute('DROP TABLE user')
    
    # Rename the old table back to the original name
    op.execute('ALTER TABLE user_new RENAME TO user')