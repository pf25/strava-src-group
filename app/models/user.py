from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.Integer, unique=True, nullable=False)
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    access_token = db.Column(db.String(100), nullable=False)
    refresh_token = db.Column(db.String(100), nullable=False)
    token_expiration = db.Column(db.DateTime, nullable=False)
    group = db.Column(db.String(20))

    def __repr__(self):
        return f'<User {self.strava_id}>'

    def token_expired(self):
        return datetime.utcnow() > self.token_expiration

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"
