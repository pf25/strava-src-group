from flask import Blueprint, render_template, redirect, url_for, session, flash, request, current_app
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from wtforms.validators import DataRequired
from app import db
from app.models import User, Activity
import requests
from datetime import datetime, timedelta
from flask_login import login_user, login_required, current_user, logout_user
from app.strava_utils import get_strava_activities
from app.utils.stats import calculate_group_stats, calculate_individual_leaderboard

bp = Blueprint('auth', __name__)

class GroupSelectionForm(FlaskForm):
    group = RadioField('Group', choices=[('North Austin', 'North Austin'), ('South Austin', 'South Austin'), ('Others', 'Others')], validators=[DataRequired()])
    submit = SubmitField('Save Selection')

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return render_template('index.html')

@bp.route('/strava_auth')
def strava_auth():
    client_id = current_app.config['STRAVA_CLIENT_ID']
    redirect_uri = url_for('auth.strava_callback', _external=True)
    return redirect(f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope=activity:read_all")

@bp.route('/strava_callback')
def strava_callback():
    code = request.args.get('code')
    client_id = current_app.config['STRAVA_CLIENT_ID']
    client_secret = current_app.config['STRAVA_CLIENT_SECRET']
    
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        user = User.query.filter_by(strava_id=data['athlete']['id']).first()
        
        if user is None:
            user = User(
                strava_id=data['athlete']['id'],
                firstname=data['athlete']['firstname'],
                lastname=data['athlete']['lastname'],
                access_token=data['access_token'],
                refresh_token=data['refresh_token'],
                token_expiration=datetime.utcnow() + timedelta(seconds=data['expires_in'])
            )
            db.session.add(user)
        else:
            user.firstname = data['athlete']['firstname']
            user.lastname = data['athlete']['lastname']
            user.access_token = data['access_token']
            user.refresh_token = data['refresh_token']
            user.token_expiration = datetime.utcnow() + timedelta(seconds=data['expires_in'])
        
        db.session.commit()
        login_user(user)
        
        if user.group:
            return redirect(url_for('auth.dashboard'))
        else:
            return redirect(url_for('auth.select_group'))
    else:
        flash("Authentication failed. Please try again.", "error")
        return redirect(url_for('auth.index'))

@bp.route('/select_group', methods=['GET', 'POST'])
@login_required
def select_group():
    form = GroupSelectionForm()
    
    if form.validate_on_submit():
        current_user.group = form.group.data
        db.session.commit()
        flash('Your group has been set successfully!', 'success')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('select_group.html', form=form)

@bp.route('/dashboard')
@login_required
def dashboard():
    recent_activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.start_date.desc()).limit(5).all()
    return render_template('dashboard.html', user=current_user, activities=recent_activities)

@bp.route('/fetch_activities')
@login_required
def fetch_activities():
    # Fetch activities from 30 days ago up to now
    success = get_strava_activities(
        current_user,
        after=datetime.utcnow() - timedelta(days=30),
        before=datetime.utcnow()
    )
    if success:
        flash('Activities fetched successfully!', 'success')
    else:
        flash('Failed to fetch activities. Please try again later.', 'error')
    return redirect(url_for('auth.dashboard'))

@bp.route('/leaderboard')
@login_required
def leaderboard():
    timeframe = request.args.get('timeframe', 'week')
    sort_by = request.args.get('sort_by', 'distance')
    group_stats = calculate_group_stats(timeframe)
    individual_leaderboard = calculate_individual_leaderboard(timeframe, sort_by)
    return render_template('leaderboard.html', 
                           group_stats=group_stats, 
                           individual_leaderboard=individual_leaderboard, 
                           timeframe=timeframe, 
                           sort_by=sort_by)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid email or password')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Clear any session data
    flash('You have been disconnected from Strava.', 'info')
    return redirect(url_for('auth.index'))

