import typer
from .gcr import app

# used for doc generation
gcr = typer.main.get_command(app)

