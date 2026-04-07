import os
from database import query_db, insert_db
from werkzeug.utils import secure_filename
from flask import current_app

def get_group_messages(group_id):
    """Fetches all messages for a specific group, joined with user info."""
    return query_db('''
        SELECT m.*, u.prn, u.name 
        FROM messages m 
        JOIN users u ON m.user_id = u.id 
        WHERE m.group_id = ? 
        ORDER BY m.created_at ASC
    ''', [group_id])

def save_message(group_id, user_id, message=None, file_url=None, file_name=None):
    """Saves a new message to the database."""
    return insert_db('''
        INSERT INTO messages (group_id, user_id, message, file_url, file_name)
        VALUES (?, ?, ?, ?, ?)
    ''', [group_id, user_id, message, file_url, file_name])

def allowed_file(filename):
    """Checks if a file extension is allowed."""
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, group_id, user_id):
    """Handles secure file saving and database recording."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add a unique prefix or directory structure to prevent collisions? 
        # Using simple approach first
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        file_url = f'/static/uploads/{filename}'
        save_message(group_id, user_id, file_url=file_url, file_name=filename)
        return file_url
    return None
