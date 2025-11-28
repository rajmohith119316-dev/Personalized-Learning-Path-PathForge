"""
Database module for user login credentials using raw SQL.
Handles all database operations for user authentication.
"""
import sqlite3
import os
from datetime import datetime
from flask_bcrypt import Bcrypt

# Initialize bcrypt (will be initialized with Flask app if needed)
bcrypt = Bcrypt()

def init_bcrypt(app):
	"""Initialize bcrypt with Flask app."""
	bcrypt.init_app(app)

# Database paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'users.db')


def init_database():
	"""Initialize the database and create tables if they don't exist."""
	os.makedirs(DATA_DIR, exist_ok=True)
	
	conn = get_connection()
	cursor = conn.cursor()
	
	# Create users table
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE NOT NULL,
			email TEXT UNIQUE NOT NULL,
			password_hash TEXT NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
	''')
	
	# Create index on email for faster lookups
	cursor.execute('''
		CREATE INDEX IF NOT EXISTS idx_email ON users(email)
	''')
	
	# Create index on username for faster lookups
	cursor.execute('''
		CREATE INDEX IF NOT EXISTS idx_username ON users(username)
	''')
	
	conn.commit()
	conn.close()
	print(f"Database initialized at: {DB_PATH}")


def get_connection():
	"""Get a database connection."""
	return sqlite3.connect(DB_PATH)


def hash_password(password):
	"""Hash a password using bcrypt."""
	return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password_hash, password):
	"""Verify a password against its hash."""
	return bcrypt.check_password_hash(password_hash, password)


def create_user(username, email, password):
	"""
	Create a new user in the database.
	
	Args:
		username: Username (must be unique)
		email: Email address (must be unique)
		password: Plain text password (will be hashed)
		
	Returns:
		dict: User data if successful, None if failed
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	try:
		password_hash = hash_password(password)
		created_at = datetime.utcnow().isoformat()
		
		cursor.execute('''
			INSERT INTO users (username, email, password_hash, created_at, last_active)
			VALUES (?, ?, ?, ?, ?)
		''', (username, email.lower(), password_hash, created_at, created_at))
		
		user_id = cursor.lastrowid
		conn.commit()
		
		return {
			'id': user_id,
			'username': username,
			'email': email.lower(),
			'created_at': created_at
		}
	except sqlite3.IntegrityError as e:
		conn.rollback()
		if 'username' in str(e):
			raise ValueError('Username already exists')
		elif 'email' in str(e):
			raise ValueError('Email already registered')
		else:
			raise ValueError('Database error')
	except Exception as e:
		conn.rollback()
		raise ValueError(f'Failed to create user: {str(e)}')
	finally:
		conn.close()


def get_user_by_email(email):
	"""
	Get user by email address.
	
	Args:
		email: Email address to search for
		
	Returns:
		dict: User data if found, None otherwise
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('''
		SELECT id, username, email, password_hash, created_at, last_active
		FROM users
		WHERE email = ?
	''', (email.lower(),))
	
	row = cursor.fetchone()
	conn.close()
	
	if row:
		return {
			'id': row[0],
			'username': row[1],
			'email': row[2],
			'password_hash': row[3],
			'created_at': row[4],
			'last_active': row[5]
		}
	return None


def get_user_by_username(username):
	"""
	Get user by username.
	
	Args:
		username: Username to search for
		
	Returns:
		dict: User data if found, None otherwise
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('''
		SELECT id, username, email, password_hash, created_at, last_active
		FROM users
		WHERE username = ?
	''', (username,))
	
	row = cursor.fetchone()
	conn.close()
	
	if row:
		return {
			'id': row[0],
			'username': row[1],
			'email': row[2],
			'password_hash': row[3],
			'created_at': row[4],
			'last_active': row[5]
		}
	return None


def get_user_by_id(user_id):
	"""
	Get user by ID.
	
	Args:
		user_id: User ID to search for
		
	Returns:
		dict: User data if found, None otherwise
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('''
		SELECT id, username, email, password_hash, created_at, last_active
		FROM users
		WHERE id = ?
	''', (user_id,))
	
	row = cursor.fetchone()
	conn.close()
	
	if row:
		return {
			'id': row[0],
			'username': row[1],
			'email': row[2],
			'password_hash': row[3],
			'created_at': row[4],
			'last_active': row[5]
		}
	return None


def update_last_active(user_id):
	"""
	Update user's last active timestamp.
	
	Args:
		user_id: User ID to update
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('''
		UPDATE users
		SET last_active = ?
		WHERE id = ?
	''', (datetime.utcnow().isoformat(), user_id))
	
	conn.commit()
	conn.close()


def authenticate_user(email, password):
	"""
	Authenticate a user with email and password.
	
	Args:
		email: User's email
		password: Plain text password
		
	Returns:
		dict: User data if authentication successful, None otherwise
	"""
	user = get_user_by_email(email)
	
	if user and verify_password(user['password_hash'], password):
		update_last_active(user['id'])
		# Remove password_hash from return
		user.pop('password_hash', None)
		return user
	
	return None


def user_exists(email=None, username=None):
	"""
	Check if a user exists by email or username.
	
	Args:
		email: Email to check (optional)
		username: Username to check (optional)
		
	Returns:
		bool: True if user exists, False otherwise
	"""
	if email:
		return get_user_by_email(email) is not None
	if username:
		return get_user_by_username(username) is not None
	return False


def get_all_users():
	"""
	Get all users from database (for admin purposes).
	
	Returns:
		list: List of user dictionaries (without password hashes)
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('''
		SELECT id, username, email, created_at, last_active
		FROM users
		ORDER BY created_at DESC
	''')
	
	rows = cursor.fetchall()
	conn.close()
	
	return [
		{
			'id': row[0],
			'username': row[1],
			'email': row[2],
			'created_at': row[3],
			'last_active': row[4]
		}
		for row in rows
	]


def delete_user(user_id):
	"""
	Delete a user from the database.
	
	Args:
		user_id: User ID to delete
		
	Returns:
		bool: True if deleted, False if user not found
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
	
	deleted = cursor.rowcount > 0
	conn.commit()
	conn.close()
	
	return deleted


def get_database_stats():
	"""
	Get statistics about the users database.
	
	Returns:
		dict: Database statistics
	"""
	conn = get_connection()
	cursor = conn.cursor()
	
	# Total users
	cursor.execute('SELECT COUNT(*) FROM users')
	total_users = cursor.fetchone()[0]
	
	# Recent registrations (last 7 days)
	cursor.execute('''
		SELECT COUNT(*) FROM users
		WHERE created_at >= datetime('now', '-7 days')
	''')
	recent_users = cursor.fetchone()[0]
	
	# Active users (active in last 30 days)
	cursor.execute('''
		SELECT COUNT(*) FROM users
		WHERE last_active >= datetime('now', '-30 days')
	''')
	active_users = cursor.fetchone()[0]
	
	conn.close()
	
	return {
		'database_path': DB_PATH,
		'database_size': os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
		'total_users': total_users,
		'recent_users': recent_users,
		'active_users': active_users
	}

