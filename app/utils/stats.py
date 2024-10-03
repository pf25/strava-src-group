from app.models import User, Activity
from sqlalchemy import func, distinct  # Add distinct here
from datetime import datetime, timedelta
from app import db

def calculate_group_stats(timeframe='week'):
    if timeframe == 'week':
        days = 7
    else:  # month
        days = 30
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    group_stats = db.session.query(
        User.group,
        func.count(distinct(User.id)).label('user_count'),
        (func.sum(Activity.distance) / func.count(distinct(User.id))).label('avg_distance'),
        (func.sum(Activity.total_elevation_gain) / func.count(distinct(User.id))).label('avg_elevation_gain'),
        (func.count(Activity.id) / func.count(distinct(User.id))).label('avg_activity_count')
    ).join(Activity).filter(
        Activity.start_date >= cutoff_date,
        Activity.type == 'Run'
    ).group_by(User.group).all()

    return [
        {
            'group': stat.group,
            'user_count': stat.user_count,
            'avg_distance': round(stat.avg_distance / 1000, 2) if stat.avg_distance else 0,  # km
            'avg_elevation_gain': round(stat.avg_elevation_gain, 2) if stat.avg_elevation_gain else 0,  # m
            'avg_activity_count': round(stat.avg_activity_count, 1) if stat.avg_activity_count else 0
        } for stat in group_stats
    ]

def calculate_individual_leaderboard(timeframe='week', sort_by='distance'):
    if timeframe == 'week':
        days = 7
    else:  # month
        days = 30
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.session.query(
        User.id,
        User.firstname,
        User.lastname,
        User.group,
        func.sum(Activity.distance).label('total_distance'),
        func.sum(Activity.total_elevation_gain).label('total_elevation_gain'),
        func.count(Activity.id).label('activity_count')
    ).join(Activity).filter(
        Activity.start_date >= cutoff_date,
        Activity.type == 'Run'
    ).group_by(User.id)

    if sort_by == 'distance':
        query = query.order_by(func.sum(Activity.distance).desc())
    elif sort_by == 'elevation':
        query = query.order_by(func.sum(Activity.total_elevation_gain).desc())
    elif sort_by == 'activities':
        query = query.order_by(func.count(Activity.id).desc())

    results = query.all()

    leaderboard = {}
    for result in results:
        if result.group not in leaderboard:
            leaderboard[result.group] = []
        leaderboard[result.group].append({
            'id': result.id,
            'name': f"{result.firstname} {result.lastname}",
            'total_distance': round(result.total_distance / 1000, 2),  # km
            'total_elevation_gain': round(result.total_elevation_gain, 2),  # m
            'activity_count': result.activity_count
        })

    return leaderboard

def calculate_individual_leaderboard(timeframe='week', sort_by='distance'):
    if timeframe == 'week':
        days = 7
    else:  # month
        days = 30
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.session.query(
        User.id,
        User.firstname,
        User.lastname,
        User.group,
        func.sum(Activity.distance).label('total_distance'),
        func.sum(Activity.total_elevation_gain).label('total_elevation_gain'),
        func.count(Activity.id).label('activity_count')
    ).join(Activity).filter(
        Activity.start_date >= cutoff_date,
        Activity.type == 'Run'
    ).group_by(User.id)

    if sort_by == 'distance':
        query = query.order_by(func.sum(Activity.distance).desc())
    elif sort_by == 'elevation':
        query = query.order_by(func.sum(Activity.total_elevation_gain).desc())
    elif sort_by == 'activities':
        query = query.order_by(func.count(Activity.id).desc())

    results = query.all()

    leaderboard = {'North Austin': [], 'South Austin': [], 'Others': []}
    for result in results:
        group = result.group if result.group in leaderboard else 'Others'
        leaderboard[group].append({
            'id': result.id,
            'name': f"{result.firstname} {result.lastname}",
            'total_distance': round(result.total_distance / 1000, 2),  # km
            'total_elevation_gain': round(result.total_elevation_gain, 2),  # m
            'activity_count': result.activity_count
        })

    return leaderboard
