import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Comment, Post, User

""" CLEAR DATABASE """


def delete_all_data():
    db.session.query(User).delete()
    db.session.query(Comment).delete()
    db.session.query(Post).delete()
    db.session.commit()


@click.command(name="delete-db-data")
@with_appcontext
def delete_db_data_command():
    delete_all_data()
    click.echo("All data has been deleted from the database.")


# app.cli.add_command(delete_db_data_command)
