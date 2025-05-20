from flask.cli import FlaskGroup
from flask_cors import CORS
from src import create_app, db

app = create_app()
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()
