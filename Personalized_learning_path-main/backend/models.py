from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json


db = SQLAlchemy()


class User(db.Model):
	__tablename__ = 'users'
	
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(80), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(255), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	last_active = db.Column(db.DateTime, default=datetime.utcnow)
	
	# Profile fields
	avatar_url = db.Column(db.String(255))
	bio = db.Column(db.Text)
	
	# Onboarding data (stored as JSON)
	current_skills = db.Column(db.Text)  # JSON array
	learning_goal = db.Column(db.String(255))
	target_role = db.Column(db.String(100))
	learning_pace = db.Column(db.String(50))
	daily_hours = db.Column(db.Float)
	preferred_content = db.Column(db.Text)  # JSON array
	assessment_score = db.Column(db.Integer)
	proficiency_level = db.Column(db.String(50))  # beginner/intermediate/advanced
	
	# Progress metrics
	total_xp = db.Column(db.Integer, default=0)
	current_level = db.Column(db.Integer, default=1)
	current_streak = db.Column(db.Integer, default=0)
	longest_streak = db.Column(db.Integer, default=0)
	total_learning_hours = db.Column(db.Float, default=0.0)
	
	# Relationships
	learning_paths = db.relationship('LearningPath', backref='user', lazy=True, cascade='all, delete-orphan')
	progress_records = db.relationship('Progress', backref='user', lazy=True, cascade='all, delete-orphan')
	achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')
	activity_logs = db.relationship('ActivityLog', backref='user', lazy=True, cascade='all, delete-orphan')
	
	def to_dict(self):
		return {
			'id': self.id,
			'username': self.username,
			'email': self.email,
			'avatar_url': self.avatar_url,
			'bio': self.bio,
			'total_xp': self.total_xp,
			'current_level': self.current_level,
			'current_streak': self.current_streak,
			'total_learning_hours': self.total_learning_hours,
			'created_at': self.created_at.isoformat(),
			'last_active': self.last_active.isoformat()
		}


class LearningPath(db.Model):
	__tablename__ = 'learning_paths'
	
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	title = db.Column(db.String(255), nullable=False)
	description = db.Column(db.Text)
	target_role = db.Column(db.String(100))
	estimated_duration_weeks = db.Column(db.Integer)
	difficulty_level = db.Column(db.String(50))
	
	# AI-generated curriculum (stored as JSON)
	curriculum_data = db.Column(db.Text, nullable=False)  # JSON with modules, topics, resources
	
	# Metadata
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
	is_active = db.Column(db.Boolean, default=True)
	ai_generated = db.Column(db.Boolean, default=True)
	generation_version = db.Column(db.String(50))
	
	# Progress metrics
	total_modules = db.Column(db.Integer, default=0)
	completed_modules = db.Column(db.Integer, default=0)
	total_topics = db.Column(db.Integer, default=0)
	completed_topics = db.Column(db.Integer, default=0)
	completion_percentage = db.Column(db.Float, default=0.0)
	
	def to_dict(self):
		return {
			'id': self.id,
			'title': self.title,
			'description': self.description,
			'target_role': self.target_role,
			'estimated_duration_weeks': self.estimated_duration_weeks,
			'difficulty_level': self.difficulty_level,
			'curriculum': json.loads(self.curriculum_data) if self.curriculum_data else {},
			'completion_percentage': self.completion_percentage,
			'total_modules': self.total_modules,
			'completed_modules': self.completed_modules,
			'total_topics': self.total_topics,
			'completed_topics': self.completed_topics,
			'created_at': self.created_at.isoformat()
		}


class Progress(db.Model):
	__tablename__ = 'progress'
	
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	learning_path_id = db.Column(db.Integer, db.ForeignKey('learning_paths.id'), nullable=False)
	
	module_id = db.Column(db.String(100), nullable=False)
	topic_id = db.Column(db.String(100), nullable=False)
	
	# Progress tracking
	status = db.Column(db.String(50), default='not_started')  # not_started, in_progress, completed
	started_at = db.Column(db.DateTime)
	completed_at = db.Column(db.DateTime)
	time_spent_minutes = db.Column(db.Integer, default=0)
	
	# User engagement
	notes = db.Column(db.Text)
	rating = db.Column(db.Integer)  # 1-5 stars
	bookmarked = db.Column(db.Boolean, default=False)
	
	# AI insights
	difficulty_feedback = db.Column(db.String(50))  # too_easy, just_right, too_hard
	ai_recommendations = db.Column(db.Text)  # JSON
	
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Achievement(db.Model):
	__tablename__ = 'achievements'
	
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), unique=True, nullable=False)
	description = db.Column(db.Text)
	icon = db.Column(db.String(100))
	category = db.Column(db.String(50))  # milestone, streak, mastery, special
	xp_reward = db.Column(db.Integer, default=0)
	rarity = db.Column(db.String(50))  # common, rare, epic, legendary
	criteria = db.Column(db.Text)  # JSON with unlock criteria


class UserAchievement(db.Model):
	__tablename__ = 'user_achievements'
	
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
	earned_at = db.Column(db.DateTime, default=datetime.utcnow)
	
	achievement = db.relationship('Achievement', backref='user_achievements')


class ActivityLog(db.Model):
	__tablename__ = 'activity_logs'
	
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	date = db.Column(db.Date, nullable=False)
	learning_minutes = db.Column(db.Integer, default=0)
	topics_completed = db.Column(db.Integer, default=0)
	xp_earned = db.Column(db.Integer, default=0)
	
	created_at = db.Column(db.DateTime, default=datetime.utcnow)
