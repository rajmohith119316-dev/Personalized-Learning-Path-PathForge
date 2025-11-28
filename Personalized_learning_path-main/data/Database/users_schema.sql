-- User Login Credentials Database Schema
-- SQLite Database for storing user authentication data

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_email ON users(email);

-- Create index on username for faster lookups
CREATE INDEX IF NOT EXISTS idx_username ON users(username);

-- Example queries:

-- Insert a new user
-- INSERT INTO users (username, email, password_hash) 
-- VALUES ('john_doe', 'john@example.com', 'hashed_password_here');

-- Get user by email
-- SELECT * FROM users WHERE email = 'john@example.com';

-- Get user by username
-- SELECT * FROM users WHERE username = 'john_doe';

-- Update last active timestamp
-- UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = 1;

-- Get all users (without password hashes)
-- SELECT id, username, email, created_at, last_active FROM users;

-- Delete a user
-- DELETE FROM users WHERE id = 1;

-- Get total user count
-- SELECT COUNT(*) FROM users;

-- Get recent users (last 7 days)
-- SELECT * FROM users WHERE created_at >= datetime('now', '-7 days');

-- Get active users (active in last 30 days)
-- SELECT * FROM users WHERE last_active >= datetime('now', '-30 days');

