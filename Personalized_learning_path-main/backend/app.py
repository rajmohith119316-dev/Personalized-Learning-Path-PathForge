from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import timedelta, datetime, date
import json
import os

from models import db, User, LearningPath, Progress, Achievement, ActivityLog, UserAchievement
from ai_engine import ai_generator, ai_recommender, ai_adaptive
from auth import validate_registration_data
from database import (
	init_database, init_bcrypt, create_user, authenticate_user, get_user_by_id,
	user_exists, update_last_active
)
from utils import calculate_streak, generate_heatmap, check_achievements, get_level_from_xp

# Compute absolute project/data paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'pathforge.db')


app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Config
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True)
db.init_app(app)

# Initialize user credentials database (SQL-based)
init_database()
init_bcrypt(app)

# Ensure main DB directory exists then create tables
with app.app_context():
	os.makedirs(DATA_DIR, exist_ok=True)
	db.create_all()


# Helpers

def _get_json():
	try:
		return request.get_json(force=True)
	except Exception:
		return {}


def _get_current_user():
	"""Get the current user from session, or return guest user."""
	user_id = session.get('user_id')
	if user_id:
		# Get from SQL database
		user_data = get_user_by_id(user_id)
		if user_data:
			update_last_active(user_id)
			# Ensure user exists in main DB for compatibility
			user = User.query.get(user_id)
			if not user:
				user = User(
					id=user_data['id'],
					username=user_data['username'],
					email=user_data['email'],
					password_hash='stored_in_users_db'
				)
				db.session.add(user)
				db.session.commit()
			return user
	
	# Return guest user if no session
	return _guest_user()

def _guest_user():
	"""Return a default guest user, creating if necessary."""
	user = User.query.filter_by(email='guest@local').first()
	if not user:
		# Create guest in SQL database too
		try:
			from database import create_user
			create_user('guest', 'guest@local', 'guest')
		except:
			pass
		user = User(username='guest', email='guest@local', password_hash='guest')
		db.session.add(user)
		db.session.commit()
	return user


# Auth Routes - Using SQL database for credentials
@app.post('/api/auth/register')
def register():
	"""Register a new user in SQL database"""
	data = _get_json()
	
	# Validate input
	errors = validate_registration_data(data)
	if errors:
		return jsonify({'message': 'Validation failed', 'errors': errors}), 400
	
	username = data.get('username', '').strip()
	email = data.get('email', '').strip().lower()
	password = data.get('password', '')
	
	# Check if username already exists
	if user_exists(username=username):
		return jsonify({'message': 'Username already exists'}), 400
	
	# Check if email already exists
	if user_exists(email=email):
		return jsonify({'message': 'Email already registered'}), 400
	
	# Create new user in SQL database
	try:
		user_data = create_user(username, email, password)
		
		# Also create in main database for compatibility
		try:
			user = User(
				id=user_data['id'],
				username=username,
				email=email,
				password_hash='stored_in_users_db'
			)
			db.session.add(user)
			db.session.commit()
		except Exception:
			pass
		
		# Set session
		session['user_id'] = user_data['id']
		
		return jsonify({
			'message': 'Registration successful',
			'user': {
				'id': user_data['id'],
				'username': user_data['username'],
				'email': user_data['email']
			}
		}), 201
	except ValueError as e:
		return jsonify({'message': str(e)}), 400
	except Exception as e:
		return jsonify({'message': 'Registration failed', 'error': str(e)}), 500


@app.post('/api/auth/login')
def login():
	"""Login user using SQL database"""
	data = _get_json()
	email = data.get('email', '').strip().lower()
	password = data.get('password', '')
	remember = data.get('remember', False)
	
	if not email or not password:
		return jsonify({'message': 'Email and password are required'}), 400
	
	# Authenticate using SQL database
	user_data = authenticate_user(email, password)
	
	if not user_data:
		return jsonify({'message': 'Invalid email or password'}), 401
	
	# Ensure user exists in main database for compatibility
	user = User.query.get(user_data['id'])
	if not user:
		user = User(
			id=user_data['id'],
			username=user_data['username'],
			email=user_data['email'],
			password_hash='stored_in_users_db'
		)
		db.session.add(user)
		db.session.commit()
	
	# Set session
	session['user_id'] = user_data['id']
	if remember:
		session.permanent = True
	
	return jsonify({
		'message': 'Login successful',
		'user': {
			'id': user_data['id'],
			'username': user_data['username'],
			'email': user_data['email']
		}
	}), 200


@app.post('/api/auth/logout')
def logout():
	"""Logout user"""
	session.pop('user_id', None)
	return jsonify({'message': 'Logged out successfully'}), 200


@app.get('/api/auth/profile')
def get_profile():
	"""Get current user profile"""
	user = _get_current_user()
	return jsonify({'user': user.to_dict()})


@app.put('/api/auth/profile')
def update_profile():
	"""Update user profile"""
	user = _get_current_user()
	data = _get_json()
	user.avatar_url = data.get('avatar_url', user.avatar_url)
	user.bio = data.get('bio', user.bio)
	db.session.commit()
	return jsonify({'user': user.to_dict()})


# Onboarding Routes
@app.post('/api/onboarding/skills')
def save_skills():
	user = _get_current_user()
	data = _get_json()
	user.current_skills = json.dumps(data.get('skills', []))
	db.session.commit()
	return jsonify({'message': 'Skills saved'})


@app.post('/api/onboarding/goal')
def save_goal():
	user = _get_current_user()
	data = _get_json()
	user.learning_goal = data.get('goal')
	user.target_role = data.get('target_role')
	db.session.commit()
	return jsonify({'message': 'Goal saved'})


@app.post('/api/onboarding/preferences')
def save_preferences():
	user = _get_current_user()
	data = _get_json()
	user.learning_pace = data.get('learning_pace')
	user.daily_hours = data.get('daily_hours')
	user.preferred_content = json.dumps(data.get('preferred_content', []))
	db.session.commit()
	return jsonify({'message': 'Preferences saved'})


@app.post('/api/onboarding/assessment')
def submit_assessment():
	user = _get_current_user()
	data = _get_json()
	score = int(data.get('score', 0))
	user.assessment_score = score
	user.proficiency_level = 'advanced' if score >= 80 else ('intermediate' if score >= 50 else 'beginner')
	db.session.commit()
	return jsonify({'message': 'Assessment saved'})


@app.get('/api/onboarding/status')
def onboarding_status():
	user = _get_current_user()
	status = {
		'skills': bool(user.current_skills),
		'goal': bool(user.learning_goal or user.target_role),
		'preferences': bool(user.learning_pace or user.daily_hours or user.preferred_content),
		'assessment': user.assessment_score is not None
	}
	return jsonify({'status': status, 'completed': all(status.values())})


# AI Learning Path Routes
@app.post('/api/ai/generate-path')
def generate_path():
	user = _get_current_user()
	current_skills = json.loads(user.current_skills or '[]')
	preferred = json.loads(user.preferred_content or '[]')
	target_role = user.target_role or 'Full Stack Developer'
	
	# Check if a path already exists for this career path
	existing_path = LearningPath.query.filter_by(
		user_id=user.id,
		target_role=target_role,
		is_active=True
	).order_by(LearningPath.created_at.desc()).first()
	
	# If path exists for this career, deactivate it and create a new one
	if existing_path:
		existing_path.is_active = False
		db.session.commit()
	
	user_data = {
		'current_skills': current_skills,
		'target_role': target_role,
		'learning_pace': user.learning_pace or 'moderate',
		'daily_hours': user.daily_hours or 2,
		'assessment_score': user.assessment_score or 0,
		'preferred_content': preferred or ['videos', 'articles', 'interactive']
	}
	curriculum = ai_generator.generate_personalized_path(user_data)
	lp = LearningPath(
		user_id=user.id,
		title=f"{curriculum.get('title', 'Learning Path')} ({target_role})",
		description=curriculum.get('description', ''),
		target_role=target_role,
		estimated_duration_weeks=curriculum.get('total_estimated_weeks', 0),
		difficulty_level=curriculum.get('difficulty', user.proficiency_level or 'beginner'),
		curriculum_data=json.dumps(curriculum),
		total_modules=len(curriculum.get('modules', [])),
		total_topics=sum(len(m.get('topics', [])) for m in curriculum.get('modules', []))
	)
	db.session.add(lp)
	db.session.commit()
	return jsonify({'path': lp.to_dict()})


@app.get('/api/ai/path/<int:user_id>')
def get_user_path(user_id):
	user = _get_current_user()
	if user.id != user_id:
		# In guest mode, always return guest path
		pass
	path = LearningPath.query.filter_by(user_id=user.id, is_active=True).order_by(LearningPath.created_at.desc()).first()
	if not path:
		return jsonify({'message': 'No path found'}), 404
	return jsonify({'path': path.to_dict()})


@app.put('/api/ai/regenerate-path')
def regenerate_path():
	user = _get_current_user()
	LearningPath.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
	db.session.commit()
	return generate_path()


@app.post('/api/ai/recommend')
def ai_recommend():
	user = _get_current_user()
	path = LearningPath.query.filter_by(user_id=user.id, is_active=True).order_by(LearningPath.created_at.desc()).first()
	if not path:
		return jsonify({'recommendations': []})
	lp = json.loads(path.curriculum_data)
	completed = [p.topic_id for p in Progress.query.filter_by(user_id=user.id, learning_path_id=path.id, status='completed').all()]
	user_skills = json.loads(user.current_skills or '[]')
	recs = ai_recommender.recommend_next_topics(completed, user_skills, lp)
	return jsonify({'recommendations': recs})


@app.post('/api/ai/adapt-path')
def adapt_path():
	user = _get_current_user()
	path = LearningPath.query.filter_by(user_id=user.id, is_active=True).order_by(LearningPath.created_at.desc()).first()
	if not path:
		return jsonify({'adaptations': {}})
	performance = [{'score': 0.8}]  # placeholder
	adaptations = ai_adaptive.adapt_curriculum(performance, json.loads(path.curriculum_data))
	return jsonify({'adaptations': adaptations})


@app.get('/api/ai/path')
def get_latest_path_guest():
	user = _get_current_user()
	path = LearningPath.query.filter_by(user_id=user.id, is_active=True).order_by(LearningPath.created_at.desc()).first()
	if not path:
		return jsonify({'message': 'No path found'}), 404
	return jsonify({'path': path.to_dict()})


# Progress Tracking Routes
@app.post('/api/progress/complete-topic')
def complete_topic():
	user = _get_current_user()
	data = _get_json()
	learning_path_id = data.get('learning_path_id')
	module_id = data.get('module_id')
	topic_id = data.get('topic_id')
	if not all([learning_path_id, module_id, topic_id]):
		return jsonify({'message': 'Missing fields'}), 400
	
	progress = Progress.query.filter_by(user_id=user.id, learning_path_id=learning_path_id, module_id=module_id, topic_id=topic_id).first()
	if not progress:
		progress = Progress(user_id=user.id, learning_path_id=learning_path_id, module_id=module_id, topic_id=topic_id)
		progress.started_at = datetime.utcnow()
	progress.status = 'completed'
	progress.completed_at = datetime.utcnow()
	progress.time_spent_minutes = data.get('time_spent_minutes', progress.time_spent_minutes or 0)
	db.session.add(progress)
	
	# Update learning path completion percentage
	path = LearningPath.query.get(learning_path_id)
	completed_topics = Progress.query.filter_by(user_id=user.id, learning_path_id=learning_path_id, status='completed').count()
	path.completed_topics = completed_topics
	if path.total_topics and path.total_topics > 0:
		path.completion_percentage = round((completed_topics / path.total_topics) * 100, 1)
	
	# Update user XP and streak
	user.total_xp += 50
	user.current_level = int(get_level_from_xp(user.total_xp))
	
	# Log activity
	log_date = date.today()
	log = ActivityLog.query.filter_by(user_id=user.id, date=log_date).first()
	if not log:
		log = ActivityLog(user_id=user.id, date=log_date)
	log.learning_minutes = (log.learning_minutes or 0) + int(data.get('time_spent_minutes', 30))
	log.topics_completed = (log.topics_completed or 0) + 1
	log.xp_earned = (log.xp_earned or 0) + 50
	db.session.add(log)
	
	db.session.commit()
	return jsonify({'message': 'Topic completed'})


@app.get('/api/progress/stats')
def progress_stats():
	user = _get_current_user()
	completed = Progress.query.filter_by(user_id=user.id, status='completed').count()
	in_progress = Progress.query.filter_by(user_id=user.id, status='in_progress').count()
	return jsonify({
		'completed_topics': completed,
		'in_progress_topics': in_progress,
		'total_xp': user.total_xp,
		'current_level': user.current_level
	})


@app.get('/api/progress/streak')
def progress_streak():
	user = _get_current_user()
	logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.date.asc()).all()
	activity_logs = [{'date': l.date.isoformat(), 'learning_minutes': l.learning_minutes} for l in logs]
	streak = calculate_streak(activity_logs)
	user.current_streak = streak
	user.longest_streak = max(user.longest_streak or 0, streak)
	db.session.commit()
	return jsonify({'current_streak': streak, 'longest_streak': user.longest_streak})


@app.post('/api/progress/activity')
def log_activity():
	user = _get_current_user()
	data = _get_json()
	log_date = datetime.fromisoformat(data.get('date')).date() if data.get('date') else date.today()
	log = ActivityLog.query.filter_by(user_id=user.id, date=log_date).first()
	if not log:
		log = ActivityLog(user_id=user.id, date=log_date)
	log.learning_minutes = int(data.get('learning_minutes', 30))
	log.topics_completed = int(data.get('topics_completed', 0))
	log.xp_earned = int(data.get('xp_earned', 0))
	db.session.add(log)
	db.session.commit()
	return jsonify({'message': 'Activity logged'})


@app.get('/api/progress/heatmap')
def progress_heatmap():
	user = _get_current_user()
	logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.date.asc()).all()
	activity_logs = [{'date': l.date.isoformat(), 'learning_minutes': l.learning_minutes} for l in logs]
	heatmap = generate_heatmap(activity_logs)
	return jsonify({'heatmap': heatmap})


# Achievement Routes
@app.get('/api/achievements/all')
def all_achievements():
	achievements = Achievement.query.all()
	return jsonify({'achievements': [
		{
			'id': a.id,
			'name': a.name,
			'description': a.description,
			'icon': a.icon,
			'category': a.category,
			'xp_reward': a.xp_reward,
			'rarity': a.rarity
		} for a in achievements
	]})


@app.get('/api/achievements/user')
def user_achievements():
	user = _get_current_user()
	uas = UserAchievement.query.filter_by(user_id=user.id).all()
	return jsonify({'achievements': [
		{
			'id': ua.achievement.id,
			'name': ua.achievement.name,
			'description': ua.achievement.description,
			'earned_at': ua.earned_at.isoformat()
		} for ua in uas
	]})


@app.post('/api/achievements/check')
def check_for_new_achievements():
	user = _get_current_user()
	completed_count = Progress.query.filter_by(user_id=user.id, status='completed').count()
	logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.date.asc()).all()
	activity_logs = [{'date': l.date.isoformat(), 'learning_minutes': l.learning_minutes} for l in logs]
	streak = calculate_streak(activity_logs)
	new = check_achievements(user, completed_count, streak)
	awarded = []
	for n in new:
		ach = Achievement.query.filter_by(name=n['name']).first()
		if not ach:
			ach = Achievement(name=n['name'], description=n['name'], category='milestone', xp_reward=n['xp'])
			db.session.add(ach)
			db.session.commit()
		if not UserAchievement.query.filter_by(user_id=user.id, achievement_id=ach.id).first():
			ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
			db.session.add(ua)
			awarded.append({'name': ach.name, 'xp': ach.xp_reward})
	
	db.session.commit()
	return jsonify({'awarded': awarded})


# Resource Routes
@app.get('/api/resources/search')
def resource_search():
	query = request.args.get('q', '')
	return jsonify({'results': [{'title': f'Resource for {query}', 'url': '#'}]})


@app.get('/api/resources/topic/<string:topic_id>')
def resources_for_topic(topic_id):
	return jsonify({'resources': [{'title': f'{topic_id} Docs', 'url': '#'}]})


@app.post('/api/resources/recommend')
def resources_recommend():
	data = _get_json()
	topic_title = data.get('topic_title', 'Topic')
	preferences = data.get('preferences', ['videos', 'articles'])
	resources = ai_recommender.recommend_resources(topic_title, preferences, data.get('difficulty', 'beginner'))
	return jsonify({'resources': resources})


# Analytics Routes
@app.get('/api/analytics/dashboard')
def analytics_dashboard():
	user = _get_current_user()
	completed = Progress.query.filter_by(user_id=user.id, status='completed').count()
	return jsonify({'summary': {'completed_topics': completed, 'total_xp': user.total_xp, 'level': user.current_level}})


@app.get('/api/analytics/learning-velocity')
def learning_velocity():
	user = _get_current_user()
	logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.date.asc()).all()
	activity_logs = [{'topics_completed': l.topics_completed, 'learning_minutes': l.learning_minutes} for l in logs]
	metrics = ai_adaptive.analyze_learning_velocity(activity_logs)
	return jsonify({'metrics': metrics})


@app.get('/api/analytics/predictions')
def analytics_predictions():
	user = _get_current_user()
	path = LearningPath.query.filter_by(user_id=user.id, is_active=True).order_by(LearningPath.created_at.desc()).first()
	if not path:
		return jsonify({'prediction': {'estimated_date': 'N/A', 'confidence': 'low'}})
	completed_topics = Progress.query.filter_by(user_id=user.id, learning_path_id=path.id, status='completed').count()
	logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.date.asc()).all()
	activity_logs = [{'topics_completed': l.topics_completed, 'learning_minutes': l.learning_minutes} for l in logs]
	velocity_info = ai_adaptive.analyze_learning_velocity(activity_logs)
	topics_per_day = velocity_info.get('topics_per_day', 0)
	prediction = ai_adaptive.predict_completion_date(completed_topics, path.total_topics or 1, topics_per_day)
	return jsonify({'prediction': prediction})


# Frontend pages
@app.get('/')
def home_page():
	from flask import render_template
	return render_template('index.html')


@app.get('/login')
def login_page():
	from flask import render_template
	return render_template('login.html')

@app.get('/learning-path')
def learning_path_page():
	from flask import render_template
	return render_template('learning-path.html')


@app.get('/register')
def register_page():
	# Redirect to onboarding since signup removed
	from flask import redirect
	return redirect('/onboarding')


@app.get('/onboarding')
def onboarding_page():
	from flask import render_template
	return render_template('onboarding.html')


@app.get('/dashboard')
def dashboard_redirect():
	return jsonify({'message': 'Dashboard coming soon'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Error handlers
@app.errorhandler(404)
def not_found(_):
    from flask import render_template
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'message': 'An unexpected error occurred'}), 500
