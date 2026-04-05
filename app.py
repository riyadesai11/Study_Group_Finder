import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db, query_db, insert_db

app = Flask(__name__)
app.secret_key = 'super_secret_study_group_key'
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.cli.command('init-db')
def init_db_command():
    init_db(app)
    print('Initialized the database.')

def get_current_user():
    if 'user_id' in session:
        return query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    return None

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

@app.route('/')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    user_subjects = query_db('''
        SELECT s.id, s.name FROM subjects s
        JOIN user_subjects us ON s.id = us.subject_id
        WHERE us.user_id = ?
    ''', (user['id'],))
    
    my_groups = query_db('''
        SELECT g.*, s.name as subject_name FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN subjects s ON g.subject_id = s.id
        WHERE gm.user_id = ?
    ''', (user['id'],))
    
    # Matching logic: Suggested groups
    suggested_groups = []
    if user_subjects:
        subject_ids = [str(s['id']) for s in user_subjects]
        placeholders = ','.join('?' * len(subject_ids))
        query = f'''
            SELECT g.*, s.name as subject_name, count(gm.user_id) as member_count 
            FROM groups g
            JOIN subjects s ON g.subject_id = s.id
            LEFT JOIN group_members gm ON g.id = gm.group_id
            WHERE g.subject_id IN ({placeholders})
            AND g.id NOT IN (
                SELECT group_id FROM group_members WHERE user_id = ?
            )
            GROUP BY g.id
        '''
        params = tuple(subject_ids) + (user['id'],)
        suggested_groups = query_db(query, params)
        
    return render_template('dashboard.html', user=user, subjects=user_subjects, my_groups=my_groups, suggested_groups=suggested_groups)

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ?', (username,), one=True)
        
        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'error')
        else:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
            
    return render_template('login.html')

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        skill_level = request.form['skill_level']
        
        user = query_db('SELECT id FROM users WHERE username = ?', (username,), one=True)
        if user is not None:
            flash('Username is already taken.', 'error')
        else:
            insert_db('INSERT INTO users (username, password_hash, skill_level) VALUES (?, ?, ?)',
                      (username, generate_password_hash(password), skill_level))
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile/subjects', methods=('GET', 'POST'))
def manage_subjects():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        subject_ids = request.form.getlist('subjects')
        
        db = get_db()
        db.execute('DELETE FROM user_subjects WHERE user_id = ?', (user['id'],))
        for sid in subject_ids:
            db.execute('INSERT INTO user_subjects (user_id, subject_id) VALUES (?, ?)', (user['id'], sid))
        db.commit()
        flash('Subjects updated successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    all_subjects = query_db('SELECT * FROM subjects')
    user_subjects = query_db('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user['id'],))
    user_subject_ids = [s['subject_id'] for s in user_subjects] if user_subjects else []
    
    return render_template('manage_subjects.html', all_subjects=all_subjects, user_subject_ids=user_subject_ids)

@app.route('/groups')
def groups():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    all_groups = query_db('''
        SELECT g.*, s.name as subject_name, count(gm.user_id) as member_count,
        (SELECT count(*) FROM group_members WHERE group_id = g.id AND user_id = ?) as is_member
        FROM groups g
        JOIN subjects s ON g.subject_id = s.id
        LEFT JOIN group_members gm ON g.id = gm.group_id
        GROUP BY g.id
    ''', (user['id'],))
    return render_template('groups.html', groups=all_groups)

@app.route('/group/create', methods=('GET', 'POST'))
def create_group():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        subject_id = request.form['subject_id']
        
        group_id = insert_db('INSERT INTO groups (name, description, subject_id, creator_id) VALUES (?, ?, ?, ?)',
                             (name, description, subject_id, user['id']))
        insert_db('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', (group_id, user['id']))
        
        flash('Group created successfully!', 'success')
        return redirect(url_for('group_detail', group_id=group_id))
        
    all_subjects = query_db('SELECT * FROM subjects')
    return render_template('create_group.html', subjects=all_subjects)

@app.route('/group/<int:group_id>')
def group_detail(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    group = query_db('''
        SELECT g.*, s.name as subject_name, u.username as creator_name
        FROM groups g
        JOIN subjects s ON g.subject_id = s.id
        JOIN users u ON g.creator_id = u.id
        WHERE g.id = ?
    ''', (group_id,), one=True)
    
    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups'))
        
    members = query_db('''
        SELECT u.username, u.skill_level, gm.joined_at
        FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
    ''', (group_id,))
    
    is_member = any(m['username'] == user['username'] for m in members)
    
    return render_template('group_detail.html', group=group, members=members, is_member=is_member)

@app.route('/group/<int:group_id>/join', methods=('POST',))
def join_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    existing = query_db('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user['id']), one=True)
    if not existing:
        insert_db('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', (group_id, user['id']))
        flash('You have joined the group!', 'success')
        
    return redirect(url_for('group_detail', group_id=group_id))

@app.route('/group/<int:group_id>/leave', methods=('POST',))
def leave_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    db = get_db()
    db.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user['id']))
    db.commit()
    flash('You have left the group.', 'success')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
