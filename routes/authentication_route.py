from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from services.authentication import authenticate_user, register_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = authenticate_user(username, password)
        if user is None:
            flash('Invalid username or password.', 'error')
        else:
            session['user_id'] = user['id']
            return redirect(url_for('main.dashboard'))
            
    return render_template('login.html')

@auth_bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        skill_level = request.form['skill_level']
        
        success, message = register_user(username, password, skill_level)
        if not success:
            flash(message, 'error')
        else:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
