from database import query_db, insert_db, get_db

def get_all_groups(user_id):
    return query_db('''
        SELECT g.*, s.name as subject_name, count(gm.user_id) as member_count,
        (SELECT count(*) FROM group_members WHERE group_id = g.id AND user_id = ?) as is_member
        FROM groups g
        JOIN subjects s ON g.subject_id = s.id
        LEFT JOIN group_members gm ON g.id = gm.group_id
        GROUP BY g.id
    ''', (user_id,))

def get_all_subjects():
    return query_db('SELECT * FROM subjects')

def create_group(name, description, subject_id, user_id):
    group_id = insert_db('INSERT INTO groups (name, description, subject_id, creator_id) VALUES (?, ?, ?, ?)',
                         (name, description, subject_id, user_id))
    insert_db('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', (group_id, user_id))
    return group_id

def get_group_details(group_id):
    return query_db('''
        SELECT g.*, s.name as subject_name, u.prn as creator_prn, u.name as creator_name
        FROM groups g
        JOIN subjects s ON g.subject_id = s.id
        JOIN users u ON g.creator_id = u.id
        WHERE g.id = ?
    ''', (group_id,), one=True)

def get_group_members(group_id):
    return query_db('''
        SELECT u.prn, u.name, u.skill_level, gm.joined_at
        FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
    ''', (group_id,))

def check_is_member(members, prn):
    return any(m['prn'] == prn for m in members)

def join_group(group_id, user_id):
    existing = query_db('SELECT * FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id), one=True)
    if not existing:
        insert_db('INSERT INTO group_members (group_id, user_id) VALUES (?, ?)', (group_id, user_id))
        return True
    return False

def leave_group(group_id, user_id):
    db = get_db()
    db.execute('DELETE FROM group_members WHERE group_id = ? AND user_id = ?', (group_id, user_id))
    db.commit()

# Dashboard logic
def get_user_subject_details(user_id):
    return query_db('''
        SELECT s.id, s.name FROM subjects s
        JOIN user_subjects us ON s.id = us.subject_id
        WHERE us.user_id = ?
    ''', (user_id,))

def get_user_groups(user_id):
    return query_db('''
        SELECT g.*, s.name as subject_name FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        JOIN subjects s ON g.subject_id = s.id
        WHERE gm.user_id = ?
    ''', (user_id,))

def get_suggested_groups(user_subjects, user_id):
    if not user_subjects:
        return []
        
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
    params = tuple(subject_ids) + (user_id,)
    return query_db(query, params)

def update_user_subjects(user_id, subject_ids):
    db = get_db()
    db.execute('DELETE FROM user_subjects WHERE user_id = ?', (user_id,))
    for sid in subject_ids:
        db.execute('INSERT INTO user_subjects (user_id, subject_id) VALUES (?, ?)', (user_id, sid))
    db.commit()

def get_user_subject_ids(user_id):
    user_subjects = query_db('SELECT subject_id FROM user_subjects WHERE user_id = ?', (user_id,))
    return [s['subject_id'] for s in user_subjects] if user_subjects else []

def is_user_in_group(user_id, group_id):
    """Checks if a specific user is a member of a group."""
    res = query_db('SELECT 1 FROM group_members WHERE user_id = ? AND group_id = ?', (user_id, group_id), one=True)
    return res is not None
