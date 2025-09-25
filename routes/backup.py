"""
Backup and restore routes for Digital Society Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
import json
import os
import tempfile
import zipfile

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
@login_required
def backup_page():
    """Backup and restore page"""
    if current_user.role != 'superadmin':
        flash('Access denied. Only super admins can access backup features.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Backup
    
    # Get all backups
    backups = Backup.query.filter_by(is_active=True).order_by(Backup.created_at.desc()).all()
    
    return render_template('backup/index.html', backups=backups)

@backup_bp.route('/create', methods=['POST'])
@login_required
def create_backup():
    """Create a new backup"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    from models import Society, Member, Receipt, User, Backup
    from app import db
    
    try:
        # Get all data
        societies = Society.query.filter_by(is_active=True).all()
        members = Member.query.filter_by(is_active=True).all()
        receipts = Receipt.query.filter_by(is_active=True).all()
        users = User.query.filter_by(is_active=True).all()
        
        # Create backup data structure
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0',
            'data': {
                'societies': [society.to_dict() for society in societies],
                'members': [member.to_dict() for member in members],
                'receipts': [receipt.to_dict() for receipt in receipts],
                'users': [{
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'society_id': user.society_id,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                } for user in users]  # Don't include password hashes
            },
            'counts': {
                'societies': len(societies),
                'members': len(members),
                'receipts': len(receipts),
                'users': len(users)
            }
        }
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'digital_society_backup_{timestamp}.json'
        
        # Create backup record
        backup = Backup(
            filename=filename,
            created_by=current_user.id,
            backup_type='manual',
            description=request.form.get('description', '').strip()
        )
        
        # Create temporary file and calculate size
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(backup_data, tmp_file, indent=2)
            tmp_file_path = tmp_file.name
        
        # Get file size
        backup.file_size = os.path.getsize(tmp_file_path)
        
        # Save backup record
        db.session.add(backup)
        db.session.commit()
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        # Store backup data in session for download (in a real app, you'd save to file system or cloud storage)
        # For this demo, we'll simulate it
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Backup created successfully!',
                'backup_id': backup.id,
                'filename': backup.filename
            })
        
        flash('Backup created successfully!', 'success')
        return redirect(url_for('backup.backup_page'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = 'An error occurred while creating the backup.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return redirect(url_for('backup.backup_page'))

@backup_bp.route('/download/<int:backup_id>')
@login_required
def download_backup(backup_id):
    """Download backup file"""
    if current_user.role != 'superadmin':
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Backup, Society, Member, Receipt, User
    
    backup = Backup.query.get_or_404(backup_id)
    
    try:
        # Recreate backup data (in a real app, you'd read from stored file)
        societies = Society.query.filter_by(is_active=True).all()
        members = Member.query.filter_by(is_active=True).all()
        receipts = Receipt.query.filter_by(is_active=True).all()
        users = User.query.filter_by(is_active=True).all()
        
        backup_data = {
            'timestamp': backup.created_at.isoformat(),
            'version': '1.0',
            'data': {
                'societies': [society.to_dict() for society in societies],
                'members': [member.to_dict() for member in members],
                'receipts': [receipt.to_dict() for receipt in receipts],
                'users': [{
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                    'society_id': user.society_id,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                } for user in users]
            },
            'counts': {
                'societies': len(societies),
                'members': len(members),
                'receipts': len(receipts),
                'users': len(users)
            }
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(backup_data, tmp_file, indent=2)
            tmp_file_path = tmp_file.name
        
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=backup.filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        flash('An error occurred while downloading the backup.', 'error')
        return redirect(url_for('backup.backup_page'))

@backup_bp.route('/restore', methods=['POST'])
@login_required
def restore_backup():
    """Restore from backup file"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    from models import Society, Member, Receipt, User
    from app import db
    
    if 'backup_file' not in request.files:
        return jsonify({'success': False, 'message': 'No backup file provided'})
    
    backup_file = request.files['backup_file']
    if backup_file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        # Read and parse backup file
        backup_content = backup_file.read().decode('utf-8')
        backup_data = json.loads(backup_content)
        
        # Validate backup format
        if 'data' not in backup_data or 'version' not in backup_data:
            return jsonify({'success': False, 'message': 'Invalid backup file format'})
        
        # WARNING: This is a destructive operation
        # In a real application, you'd want additional confirmation and possibly create a backup first
        
        # Clear existing data (soft delete)
        Society.query.update({'is_active': False})
        Member.query.update({'is_active': False})
        Receipt.query.update({'is_active': False})
        User.query.filter(User.role != 'superadmin').update({'is_active': False})
        
        # Restore societies
        society_id_mapping = {}  # Map old IDs to new IDs
        for society_data in backup_data['data'].get('societies', []):
            society = Society(
                name=society_data['name'],
                address=society_data.get('address', ''),
                registration_number=society_data['registration_number'],
                registration_year=society_data['registration_year'],
                signature_authority=society_data.get('signature_authority'),
                signature_type=society_data.get('signature_type', 'text'),
                signature_text=society_data.get('signature_text'),
                signature_image=society_data.get('signature_image')
            )
            db.session.add(society)
            db.session.flush()  # Get the new ID
            society_id_mapping[society_data['id']] = society.id
        
        # Restore members
        member_id_mapping = {}
        for member_data in backup_data['data'].get('members', []):
            if member_data['society_id'] in society_id_mapping:
                member = Member(
                    name=member_data['name'],
                    country_code=member_data['country_code'],
                    phone=member_data['phone'],
                    building=member_data['building'],
                    apartment=member_data['apartment'],
                    society_id=society_id_mapping[member_data['society_id']],
                    monthly_maintenance=member_data['monthly_maintenance'],
                    monthly_water_bill=member_data['monthly_water_bill'],
                    dues_from_month=member_data.get('dues_from_month'),
                    dues_from_year=member_data.get('dues_from_year')
                )
                
                if member_data.get('other_bills'):
                    member.other_bills_list = member_data['other_bills']
                
                db.session.add(member)
                db.session.flush()
                member_id_mapping[member_data['id']] = member.id
        
        # Restore receipts
        for receipt_data in backup_data['data'].get('receipts', []):
            if (receipt_data['society_id'] in society_id_mapping and 
                receipt_data['member_id'] in member_id_mapping):
                
                receipt = Receipt(
                    receipt_number=receipt_data['receipt_number'],
                    date=datetime.fromisoformat(receipt_data['date']),
                    member_id=member_id_mapping[receipt_data['member_id']],
                    society_id=society_id_mapping[receipt_data['society_id']],
                    total_amount=receipt_data['total_amount'],
                    payment_from_month=receipt_data['payment_from_month'],
                    payment_from_year=receipt_data['payment_from_year'],
                    payment_till_month=receipt_data['payment_till_month'],
                    payment_till_year=receipt_data['payment_till_year'],
                    description=receipt_data.get('description')
                )
                
                if receipt_data.get('items'):
                    receipt.items_list = receipt_data['items']
                
                db.session.add(receipt)
        
        # Restore users (excluding superadmins and passwords)
        for user_data in backup_data['data'].get('users', []):
            if (user_data['role'] != 'superadmin' and 
                user_data.get('society_id') in society_id_mapping):
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=user_data['email']).first()
                if existing_user:
                    # Reactivate existing user
                    existing_user.is_active = True
                    existing_user.society_id = society_id_mapping[user_data['society_id']]
                else:
                    # Create new user (they'll need to reset password)
                    user = User(
                        email=user_data['email'],
                        role=user_data['role'],
                        society_id=society_id_mapping[user_data['society_id']],
                        is_active=True
                    )
                    user.set_password('password123')  # Default password - user should change
                    db.session.add(user)
        
        db.session.commit()
        
        counts = backup_data.get('counts', {})
        message = f'Backup restored successfully! Restored {counts.get("societies", 0)} societies, {counts.get("members", 0)} members, {counts.get("receipts", 0)} receipts, and {counts.get("users", 0)} users.'
        
        return jsonify({'success': True, 'message': message})
        
    except json.JSONDecodeError:
        return jsonify({'success': False, 'message': 'Invalid JSON file format'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while restoring the backup'})

@backup_bp.route('/<int:backup_id>/delete', methods=['POST'])
@login_required
def delete_backup(backup_id):
    """Delete backup record"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    from models import Backup
    from app import db
    
    backup = Backup.query.get_or_404(backup_id)
    
    try:
        # Soft delete
        backup.is_active = False
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Backup deleted successfully'})
        
        flash('Backup deleted successfully', 'success')
        return redirect(url_for('backup.backup_page'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = 'An error occurred while deleting the backup.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return redirect(url_for('backup.backup_page'))