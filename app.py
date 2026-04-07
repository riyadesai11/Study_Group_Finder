import os
from flask import Flask, g
from flask_socketio import SocketIO, join_room, leave_room, emit
from database import init_db
from services.authentication import get_current_user
from services.chat import save_message
from services.groups import is_user_in_group

# Import blueprints
from routes.authentication_route import auth_bp
from routes.groups_route import groups_bp
from routes.main_route import main_bp

app = Flask(__name__)
app.secret_key = 'super_secret_study_group_key'
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('join')
def on_join(data):
    user = get_current_user()
    group_id = data.get('group_id')
    
    if user and group_id and is_user_in_group(user['id'], group_id):
        room = str(group_id)
        join_room(room)
        print(f"Authorized: User {user['prn']} joined room {room}")
    else:
        print(f"Unauthorized join attempt for group {group_id}")

@socketio.on('leave')
def on_leave(data):
    room = str(data['group_id'])
    leave_room(room)

@socketio.on('send_message')
def on_send_message(data):
    user = get_current_user()
    group_id = data.get('group_id')
    message_text = data.get('message')
    
    if not user or not group_id or not is_user_in_group(user['id'], group_id):
        print(f"Unauthorized send attempt for group {group_id}")
        return
    
    # Save to database
    save_message(group_id, user['id'], message=message_text)
    
    # Broadcast to everyone in the room
    emit('receive_message', {
        'prn': user['prn'],
        'name': user['name'],
        'message': message_text,
        'created_at': 'Just now'
    }, room=str(group_id))

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.cli.command('init-db')
def init_db_command():
    init_db(app)
    print('Initialized the database.')

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
