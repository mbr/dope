import click

from .model import db
from . import create_app


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = create_app()


@cli.command('reset-db', help='Recreate the database, dropping existing data.')
@click.pass_obj
def reset_db(obj):
    with obj.app_context():
        obj.config['SQLALCHEMY_ECHO'] = True
        db.drop_all()
        db.create_all()
