from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from .config import Config
# from flask_migrate import Migrate


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy()

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def hello_world():
    return 'Hello, World!'