import click
from flask import current_app
from .db import DBConnector

db = DBConnector()

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    db.init_app(current_app)
    with current_app.open_resource('schema.sql') as f:
        connection = db.connect()
        with connection.cursor() as cursor:
            for statement in f.read().decode('utf8').split(';'):
                if statement.strip():
                    cursor.execute(statement)
        connection.commit()
    click.echo('Initialized the database.')