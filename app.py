import os
from flask import Flask, g
from database import init_db
from services.authentication import get_current_user

# Import blueprints
from routes.authentication_route import auth_bp
from routes.groups_route import groups_bp
from routes.main_route import main_bp

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

@app.context_processor
def inject_user():
    return dict(current_user=get_current_user())

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(groups_bp)
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
