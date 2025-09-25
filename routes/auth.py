"""
Authentication routes for Digital Society Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if current_user.is_authenticated:
        if current_user.role == 'superadmin':
            return redirect(url_for('dashboard.superadmin_dashboard'))
        else:
            return redirect(url_for('dashboard.admin_dashboard'))
    
    if request.method == 'POST':
        from models import User
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email and password are required'})
            flash('Email and password are required', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            
            if request.is_json:
                redirect_url = next_page or (
                    url_for('dashboard.superadmin_dashboard') if user.role == 'superadmin' 
                    else url_for('dashboard.admin_dashboard')
                )
                return jsonify({'success': True, 'redirect': redirect_url})
            
            flash(f'Welcome back, {user.email}!', 'success')
            return redirect(next_page or (
                url_for('dashboard.superadmin_dashboard') if user.role == 'superadmin' 
                else url_for('dashboard.admin_dashboard')
            ))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid email or password'})
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        from models import User, Society
        from app import db
        
        data = request.get_json() if request.is_json else request.form
        
        # Extract form data
        society_name = data.get('society_name', '').strip()
        registration_number = data.get('registration_number', '').strip()
        registration_year = data.get('registration_year', '')
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        errors = []
        
        if not society_name:
            errors.append('Society name is required')
        elif len(society_name) < 2:
            errors.append('Society name must be at least 2 characters long')
        elif Society.query.filter_by(name=society_name).first():
            errors.append('A society with this name already exists')
        
        if not registration_number:
            errors.append('Registration number is required')
        elif Society.query.filter_by(registration_number=registration_number).first():
            errors.append('A society with this registration number already exists')
        
        try:
            registration_year = int(registration_year)
            if registration_year < 1900 or registration_year > 2030:
                errors.append('Please enter a valid registration year')
        except (ValueError, TypeError):
            errors.append('Please enter a valid registration year')
        
        if not email:
            errors.append('Email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')
        elif User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors})
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        try:
            # Create society
            society = Society(
                name=society_name,
                registration_number=registration_number,
                registration_year=registration_year
            )
            db.session.add(society)
            db.session.flush()  # Get the society ID
            
            # Create user
            user = User(
                email=email,
                role='admin',
                society_id=society.id
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Account created successfully!',
                    'redirect': url_for('dashboard.admin_dashboard')
                })
            
            flash('Account created successfully! Welcome to Digital Society Management.', 'success')
            return redirect(url_for('dashboard.admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred while creating your account. Please try again.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            flash(error_msg, 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        from models import User
        
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        
        if not email:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email is required'})
            flash('Email is required', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        # Always show success message for security (don't reveal if email exists)
        success_msg = 'If an account with this email exists, you will receive password reset instructions.'
        
        if user:
            # In a real application, you would send an email with a reset token
            # For this demo, we'll simulate the email in the session
            session['simulated_email'] = {
                'subject': 'Password Reset Instructions',
                'body': f'Hello {user.email},\n\nWe received a request to reset your password.\n\nFor this demonstration, your current password is: [Hidden for security]\n\nIn a real application, you would receive a secure link to reset your password.\n\nIf you did not request this reset, please ignore this email.',
                'to': user.email
            }
        
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg})
        
        flash(success_msg, 'info')
        return render_template('auth/forgot_password.html', email_sent=True)
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout handler"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/check-society-name')
def check_society_name():
    """API endpoint to check if society name exists"""
    from models import Society
    
    name = request.args.get('name', '').strip()
    if not name:
        return jsonify({'exists': False})
    
    exists = Society.query.filter_by(name=name).first() is not None
    return jsonify({'exists': exists})

@auth_bp.route('/check-registration-number')
def check_registration_number():
    """API endpoint to check if registration number exists"""
    from models import Society
    
    reg_number = request.args.get('registration_number', '').strip()
    if not reg_number:
        return jsonify({'exists': False})
    
    exists = Society.query.filter_by(registration_number=reg_number).first() is not None
    return jsonify({'exists': exists})