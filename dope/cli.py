import click


@click.group()
def cli():
    pass


@cli.command()
def init_db():
    pass
