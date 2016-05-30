"""The main app for NHS Tutoring.

    All config settings are in config.py
    To run the server, just execute run.py
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from app import views