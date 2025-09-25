"""
Digital Society Management System
Flask Application Entry Point
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import uuid
from typing import Dict, List, Optional, Any

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///digital_society.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize models and database
from models import db
db.init_app(app)

# Initialize other extensions
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
CORS(app)

# Import models after db initialization
from models import User, Society, Member, Receipt, Backup
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.societies import societies_bp
from routes.members import members_bp
from routes.receipts import receipts_bp
from routes.backup import backup_bp
from routes.api import api_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(societies_bp, url_prefix='/societies')
app.register_blueprint(members_bp, url_prefix='/members')
app.register_blueprint(receipts_bp, url_prefix='/receipts')
app.register_blueprint(backup_bp, url_prefix='/backup')
app.register_blueprint(api_bp, url_prefix='/api')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Main application route"""
    if current_user.is_authenticated:
        if current_user.role == 'superadmin':
            return redirect(url_for('dashboard.superadmin_dashboard'))
        else:
            return redirect(url_for('dashboard.admin_dashboard'))
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.context_processor
def utility_processor():
    """Inject utility functions into templates"""
    def format_currency(amount):
        return f"${amount:,.2f}"
    
    def format_date(date):
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        return date.strftime('%B %d, %Y')
    
    def format_datetime(date):
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        return date.strftime('%B %d, %Y at %I:%M %p')
    
    return dict(
        format_currency=format_currency,
        format_date=format_date,
        format_datetime=format_datetime
    )

def create_default_superadmin():
    """Create default superadmin user if none exists"""
    if not User.query.filter_by(role='superadmin').first():
        superadmin = User(
            email='admin@gmail.com',
            role='superadmin'
        )
        superadmin.set_password('password')
        db.session.add(superadmin)
        db.session.commit()
        print("Default superadmin user created: admin@gmail.com / password")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_superadmin()
    
    app.run(debug=True, host='0.0.0.0', port=5000)