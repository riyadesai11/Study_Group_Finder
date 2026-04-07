from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, insert_db
from flask import session

import re

def get_current_user():
    if 'user_id' in session:
        return query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    return None

def authenticate_user(prn, password):
    user = query_db('SELECT * FROM users WHERE prn = ?', (prn,), one=True)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None

def register_user(prn, password, skill_level):
    if not re.match(r'^2602403250(0[1-9]|[1-8][0-9])$', prn):
        return False, 'Invalid Student ID. Must be between 260240325001 and 260240325089.'
        
    user = query_db('SELECT id FROM users WHERE prn = ?', (prn,), one=True)
    if user is not None:
        return False, 'PRN is already registered.'
    
    insert_db('INSERT INTO users (prn, password_hash, skill_level) VALUES (?, ?, ?)',
              (prn, generate_password_hash(password), skill_level))
    return True, 'Registration successful! Please login.'
