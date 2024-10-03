from app import db
from datetime import datetime

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.Integer, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Make sure this line is present
    distance = db.Column(db.Float, nullable=False)
    moving_time = db.Column(db.Integer, nullable=False)
    elapsed_time = db.Column(db.Integer, nullable=False)
    total_elevation_gain = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

    def __repr__(self):
        return f'<Activity {self.strava_id}>'
