from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, insert_db
from flask import session

def get_current_user():
    if 'user_id' in session:
        return query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    return None

def authenticate_user(username, password):
    user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def register_user(username, password, skill_level):
    user = query_db('SELECT id FROM users WHERE username = ?', (username,), one=True)
    if user is not None:
        return False, 'Username is already taken.'
    
    insert_db('INSERT INTO users (username, password_hash, skill_level) VALUES (?, ?, ?)',
              (username, generate_password_hash(password), skill_level))
    return True, 'Registration successful! Please login.'
