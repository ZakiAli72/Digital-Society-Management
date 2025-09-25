"""
Society management routes for Digital Society Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

societies_bp = Blueprint('societies', __name__)

@societies_bp.route('/')
@login_required
def list_societies():
    """List all societies (superadmin only)"""
    if current_user.role != 'superadmin':
        return redirect(url_for('societies.profile'))
    
    from models import Society, Member, Receipt
    from sqlalchemy import func
    
    # Get all societies with statistics
    societies_data = []
    societies = Society.query.filter_by(is_active=True).order_by(Society.created_at.desc()).all()
    
    for society in societies:
        member_count = Member.query.filter_by(society_id=society.id, is_active=True).count()
        receipt_count = Receipt.query.filter_by(society_id=society.id, is_active=True).count()
        total_revenue = Receipt.query.filter_by(society_id=society.id, is_active=True).with_entities(
            func.sum(Receipt.total_amount)
        ).scalar() or 0
        
        societies_data.append({
            'society': society,
            'member_count': member_count,
            'receipt_count': receipt_count,
            'total_revenue': total_revenue
        })
    
    return render_template('societies/list.html', societies_data=societies_data)

@societies_bp.route('/profile')
@login_required
def profile():
    """View/edit society profile"""
    if current_user.role == 'superadmin':
        return redirect(url_for('societies.list_societies'))
    
    if not current_user.society_id:
        flash('No society associated with your account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Society
    
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    return render_template('societies/profile.html', society=society)

@societies_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit society profile"""
    if current_user.role == 'superadmin':
        return redirect(url_for('societies.list_societies'))
    
    if not current_user.society_id:
        flash('No society associated with your account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Society
    from app import db
    
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Update society information
        society.name = data.get('name', '').strip()
        society.address = data.get('address', '').strip()
        society.registration_number = data.get('registration_number', '').strip()
        society.signature_authority = data.get('signature_authority', '').strip()
        society.signature_type = data.get('signature_type', 'text')
        society.signature_text = data.get('signature_text', '').strip()
        
        # Handle registration year
        try:
            society.registration_year = int(data.get('registration_year', society.registration_year))
        except (ValueError, TypeError):
            if request.is_json:
                return jsonify({'success': False, 'message': 'Invalid registration year'})
            flash('Invalid registration year', 'error')
            return render_template('societies/edit.html', society=society)
        
        # Handle signature image (base64)
        if society.signature_type == 'image':
            signature_image = data.get('signature_image', '')
            if signature_image:
                society.signature_image = signature_image
        else:
            society.signature_image = None
        
        # Validation
        errors = []
        
        if not society.name:
            errors.append('Society name is required')
        elif len(society.name) < 2:
            errors.append('Society name must be at least 2 characters long')
        
        # Check if name already exists (excluding current society)
        existing_society = Society.query.filter(
            Society.name == society.name,
            Society.id != society.id
        ).first()
        if existing_society:
            errors.append('A society with this name already exists')
        
        if not society.registration_number:
            errors.append('Registration number is required')
        
        # Check if registration number already exists (excluding current society)
        existing_reg = Society.query.filter(
            Society.registration_number == society.registration_number,
            Society.id != society.id
        ).first()
        if existing_reg:
            errors.append('A society with this registration number already exists')
        
        if society.registration_year < 1900 or society.registration_year > 2030:
            errors.append('Please enter a valid registration year')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors})
            for error in errors:
                flash(error, 'error')
            return render_template('societies/edit.html', society=society)
        
        try:
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Society profile updated successfully!'})
            
            flash('Society profile updated successfully!', 'success')
            return redirect(url_for('societies.profile'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred while updating the society profile.'
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            flash(error_msg, 'error')
    
    return render_template('societies/edit.html', society=society)

@societies_bp.route('/<int:society_id>')
@login_required
def view_society(society_id):
    """View specific society details (superadmin only)"""
    if current_user.role != 'superadmin':
        return redirect(url_for('societies.profile'))
    
    from models import Society, Member, Receipt, User
    from sqlalchemy import func
    
    society = Society.query.get_or_404(society_id)
    
    # Get society statistics
    member_count = Member.query.filter_by(society_id=society.id, is_active=True).count()
    receipt_count = Receipt.query.filter_by(society_id=society.id, is_active=True).count()
    total_revenue = Receipt.query.filter_by(society_id=society.id, is_active=True).with_entities(
        func.sum(Receipt.total_amount)
    ).scalar() or 0
    
    # Get society admin users
    admin_users = User.query.filter_by(society_id=society.id, is_active=True).all()
    
    # Get recent members and receipts
    recent_members = Member.query.filter_by(
        society_id=society.id, is_active=True
    ).order_by(Member.created_at.desc()).limit(10).all()
    
    recent_receipts = Receipt.query.filter_by(
        society_id=society.id, is_active=True
    ).order_by(Receipt.date.desc()).limit(10).all()
    
    return render_template('societies/view.html', 
                         society=society,
                         stats={
                             'member_count': member_count,
                             'receipt_count': receipt_count,
                             'total_revenue': total_revenue
                         },
                         admin_users=admin_users,
                         recent_members=recent_members,
                         recent_receipts=recent_receipts)

@societies_bp.route('/<int:society_id>/delete', methods=['POST'])
@login_required
def delete_society(society_id):
    """Delete society (superadmin only)"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    from models import Society, Member, Receipt, User
    from app import db
    
    society = Society.query.get_or_404(society_id)
    
    try:
        # Get counts before deletion for the confirmation message
        member_count = Member.query.filter_by(society_id=society.id).count()
        receipt_count = Receipt.query.filter_by(society_id=society.id).count()
        user_count = User.query.filter_by(society_id=society.id).count()
        
        # Soft delete - mark as inactive instead of hard delete
        society.is_active = False
        
        # Also deactivate all related records
        Member.query.filter_by(society_id=society.id).update({'is_active': False})
        Receipt.query.filter_by(society_id=society.id).update({'is_active': False})
        User.query.filter_by(society_id=society.id).update({'is_active': False})
        
        db.session.commit()
        
        message = f'Society "{society.name}" and all associated data ({member_count} members, {receipt_count} receipts, {user_count} users) have been deleted.'
        
        if request.is_json:
            return jsonify({'success': True, 'message': message})
        
        flash(message, 'success')
        return redirect(url_for('societies.list_societies'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = 'An error occurred while deleting the society.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return redirect(url_for('societies.view_society', society_id=society_id))

@societies_bp.route('/api/search')
@login_required
def api_search_societies():
    """API endpoint to search societies"""
    if current_user.role != 'superadmin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import Society
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    societies = Society.query.filter_by(is_active=True).filter(
        Society.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify([{
        'id': society.id,
        'name': society.name,
        'registration_number': society.registration_number,
        'registration_year': society.registration_year
    } for society in societies])