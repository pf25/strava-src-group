import requests
from flask import current_app
from app import db
from app.models import User, Activity
from datetime import datetime, timedelta

def get_strava_activities(user, after=None, before=None):
    if user.token_expired():
        from flask import current_app
        with current_app.app_context():
            refresh_access_token(user)

    headers = {'Authorization': f'Bearer {user.access_token}'}
    params = {
        'per_page': 30,
        'page': 1
    }
    if after:
        params['after'] = int(after.timestamp())
    if before:
        params['before'] = int(before.timestamp())
    else:
        # If 'before' is not set, use the current time
        params['before'] = int(datetime.utcnow().timestamp())

    response = requests.get('https://www.strava.com/api/v3/athlete/activities', headers=headers, params=params)
    
    if response.status_code == 200:
        activities_data = response.json()
        for activity_data in activities_data:
            if activity_data['type'] == 'Run':  # Only process run activities
                existing_activity = Activity.query.filter_by(strava_id=activity_data['id']).first()
                if not existing_activity:
                    activity = Activity(
                        strava_id=activity_data['id'],
                        user_id=user.id,
                        name=activity_data['name'],
                        type=activity_data['type'],  # Add this line
                        distance=activity_data['distance'],
                        moving_time=activity_data['moving_time'],
                        elapsed_time=activity_data['elapsed_time'],
                        total_elevation_gain=activity_data['total_elevation_gain'],
                        start_date=datetime.strptime(activity_data['start_date'], '%Y-%m-%dT%H:%M:%SZ')
                    )
                    db.session.add(activity)
        db.session.commit()
        return True
    return False

def refresh_access_token(user):
    from flask import current_app  # Import here to avoid circular import issues

    data = {
        'client_id': current_app.config['STRAVA_CLIENT_ID'],
        'client_secret': current_app.config['STRAVA_CLIENT_SECRET'],
        'grant_type': 'refresh_token',
        'refresh_token': user.refresh_token
    }
    response = requests.post('https://www.strava.com/oauth/token', data=data)
    if response.status_code == 200:
        token_data = response.json()
        user.access_token = token_data['access_token']
        user.refresh_token = token_data['refresh_token']
        user.token_expiration = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        db.session.commit()
        return True
    return False

# This function ensures refresh_access_token is called within an app context
def refresh_token_wrapper(app, user):
    with app.app_context():
        return refresh_access_token(user)
