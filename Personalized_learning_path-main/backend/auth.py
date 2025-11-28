from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()


def hash_password(password):
	"""Hash a password for storing"""
	return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(password_hash, password):
	"""Verify a stored password against one provided by user"""
	return bcrypt.check_password_hash(password_hash, password)


def validate_registration_data(data):
	"""Validate user registration data"""
	errors = []
	
	if not data.get('username') or len(data.get('username', '')) < 3:
		errors.append('Username must be at least 3 characters')
	
	if not data.get('email') or '@' not in data.get('email', ''):
		errors.append('Valid email is required')
	
	if not data.get('password') or len(data.get('password', '')) < 6:
		errors.append('Password must be at least 6 characters')
	
	return errors
