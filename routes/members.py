"""
Member management routes for Digital Society Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json
import re

members_bp = Blueprint('members', __name__)

@members_bp.route('/')
@login_required
def list_members():
    """List members"""
    from models import Member, Society
    
    if current_user.role == 'superadmin':
        # Super admin sees all members
        page = request.args.get('page', 1, type=int)
        society_id = request.args.get('society_id', type=int)
        search = request.args.get('search', '').strip()
        
        query = Member.query.filter_by(is_active=True)
        
        if society_id:
            query = query.filter_by(society_id=society_id)
        
        if search:
            query = query.filter(Member.name.ilike(f'%{search}%'))
        
        members = query.order_by(Member.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        societies = Society.query.filter_by(is_active=True).all()
        
    elif current_user.role == 'admin' and current_user.society_id:
        # Admin sees only their society members
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = Member.query.filter_by(society_id=current_user.society_id, is_active=True)
        
        if search:
            query = query.filter(Member.name.ilike(f'%{search}%'))
        
        members = query.order_by(Member.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        societies = [Society.query.get(current_user.society_id)]
        
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    return render_template('members/list.html', 
                         members=members, 
                         societies=societies,
                         selected_society_id=request.args.get('society_id', type=int),
                         search_query=request.args.get('search', ''))

@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_member():
    """Add new member"""
    if current_user.role == 'superadmin':
        flash('Super admins cannot add members directly. Please use a society admin account.', 'error')
        return redirect(url_for('members.list_members'))
    
    if not current_user.society_id:
        flash('No society associated with your account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Member, Society
    from app import db
    
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Extract form data
        name = data.get('name', '').strip()
        country_code = data.get('country_code', '+1').strip()
        phone = data.get('phone', '').strip()
        building = data.get('building', '').strip()
        apartment = data.get('apartment', '').strip()
        monthly_maintenance = data.get('monthly_maintenance', 0)
        monthly_water_bill = data.get('monthly_water_bill', 0)
        dues_from_month = data.get('dues_from_month', None)
        dues_from_year = data.get('dues_from_year', None)
        
        # Handle other bills
        other_bills = []
        if 'other_bills' in data:
            if isinstance(data['other_bills'], str):
                try:
                    other_bills = json.loads(data['other_bills'])
                except:
                    other_bills = []
            else:
                other_bills = data['other_bills']
        
        # Validation
        errors = []
        
        if not name:
            errors.append('Member name is required')
        elif len(name) < 2:
            errors.append('Member name must be at least 2 characters long')
        
        if not phone:
            errors.append('Phone number is required')
        elif not re.match(r'^[0-9+\-\s()]{7,15}$', phone):
            errors.append('Please enter a valid phone number')
        
        if not building:
            errors.append('Building is required')
        
        if not apartment:
            errors.append('Apartment is required')
        
        try:
            monthly_maintenance = float(monthly_maintenance)
            if monthly_maintenance < 0:
                errors.append('Monthly maintenance cannot be negative')
        except (ValueError, TypeError):
            monthly_maintenance = 0
        
        try:
            monthly_water_bill = float(monthly_water_bill)
            if monthly_water_bill < 0:
                errors.append('Monthly water bill cannot be negative')
        except (ValueError, TypeError):
            monthly_water_bill = 0
        
        # Validate dues dates
        if dues_from_month:
            try:
                dues_from_month = int(dues_from_month)
                if dues_from_month < 1 or dues_from_month > 12:
                    errors.append('Dues from month must be between 1 and 12')
            except (ValueError, TypeError):
                dues_from_month = None
        
        if dues_from_year:
            try:
                dues_from_year = int(dues_from_year)
                if dues_from_year < 2020 or dues_from_year > 2030:
                    errors.append('Please enter a valid dues year')
            except (ValueError, TypeError):
                dues_from_year = None
        
        # Validate other bills
        for i, bill in enumerate(other_bills):
            if not isinstance(bill, dict) or 'name' not in bill or 'amount' not in bill:
                errors.append(f'Invalid other bill format at position {i+1}')
                continue
            
            if not bill['name'].strip():
                errors.append(f'Other bill name is required at position {i+1}')
            
            try:
                bill['amount'] = float(bill['amount'])
                if bill['amount'] < 0:
                    errors.append(f'Other bill amount cannot be negative at position {i+1}')
            except (ValueError, TypeError):
                errors.append(f'Invalid other bill amount at position {i+1}')
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors})
            for error in errors:
                flash(error, 'error')
            return render_template('members/add.html', society=society)
        
        try:
            member = Member(
                name=name,
                country_code=country_code,
                phone=phone,
                building=building,
                apartment=apartment,
                society_id=society.id,
                monthly_maintenance=monthly_maintenance,
                monthly_water_bill=monthly_water_bill,
                dues_from_month=dues_from_month,
                dues_from_year=dues_from_year
            )
            
            if other_bills:
                member.other_bills_list = other_bills
            
            db.session.add(member)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Member added successfully!',
                    'member_id': member.id
                })
            
            flash('Member added successfully!', 'success')
            return redirect(url_for('members.list_members'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred while adding the member.'
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            flash(error_msg, 'error')
    
    return render_template('members/add.html', society=society)

@members_bp.route('/<int:member_id>')
@login_required
def view_member(member_id):
    """View member details"""
    from models import Member, Receipt
    
    member = Member.query.get_or_404(member_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != member.society_id:
            flash('Access denied.', 'error')
            return redirect(url_for('members.list_members'))
    
    # Get member's receipts
    receipts = Receipt.query.filter_by(
        member_id=member.id, 
        is_active=True
    ).order_by(Receipt.date.desc()).all()
    
    return render_template('members/view.html', member=member, receipts=receipts)

@members_bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    """Edit member"""
    from models import Member
    from app import db
    
    member = Member.query.get_or_404(member_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != member.society_id:
            flash('Access denied.', 'error')
            return redirect(url_for('members.list_members'))
    elif current_user.role == 'superadmin':
        flash('Super admins cannot edit members directly. Please use a society admin account.', 'error')
        return redirect(url_for('members.view_member', member_id=member_id))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Update member data (similar validation as add_member)
        name = data.get('name', '').strip()
        country_code = data.get('country_code', '+1').strip()
        phone = data.get('phone', '').strip()
        building = data.get('building', '').strip()
        apartment = data.get('apartment', '').strip()
        monthly_maintenance = data.get('monthly_maintenance', 0)
        monthly_water_bill = data.get('monthly_water_bill', 0)
        dues_from_month = data.get('dues_from_month', None)
        dues_from_year = data.get('dues_from_year', None)
        
        # Handle other bills
        other_bills = []
        if 'other_bills' in data:
            if isinstance(data['other_bills'], str):
                try:
                    other_bills = json.loads(data['other_bills'])
                except:
                    other_bills = []
            else:
                other_bills = data['other_bills']
        
        # Validation (same as add_member)
        errors = []
        
        if not name:
            errors.append('Member name is required')
        elif len(name) < 2:
            errors.append('Member name must be at least 2 characters long')
        
        if not phone:
            errors.append('Phone number is required')
        elif not re.match(r'^[0-9+\-\s()]{7,15}$', phone):
            errors.append('Please enter a valid phone number')
        
        if not building:
            errors.append('Building is required')
        
        if not apartment:
            errors.append('Apartment is required')
        
        try:
            monthly_maintenance = float(monthly_maintenance)
            if monthly_maintenance < 0:
                errors.append('Monthly maintenance cannot be negative')
        except (ValueError, TypeError):
            monthly_maintenance = 0
        
        try:
            monthly_water_bill = float(monthly_water_bill)
            if monthly_water_bill < 0:
                errors.append('Monthly water bill cannot be negative')
        except (ValueError, TypeError):
            monthly_water_bill = 0
        
        if dues_from_month:
            try:
                dues_from_month = int(dues_from_month)
                if dues_from_month < 1 or dues_from_month > 12:
                    errors.append('Dues from month must be between 1 and 12')
            except (ValueError, TypeError):
                dues_from_month = None
        
        if dues_from_year:
            try:
                dues_from_year = int(dues_from_year)
                if dues_from_year < 2020 or dues_from_year > 2030:
                    errors.append('Please enter a valid dues year')
            except (ValueError, TypeError):
                dues_from_year = None
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors})
            for error in errors:
                flash(error, 'error')
            return render_template('members/edit.html', member=member)
        
        try:
            # Update member
            member.name = name
            member.country_code = country_code
            member.phone = phone
            member.building = building
            member.apartment = apartment
            member.monthly_maintenance = monthly_maintenance
            member.monthly_water_bill = monthly_water_bill
            member.dues_from_month = dues_from_month
            member.dues_from_year = dues_from_year
            member.other_bills_list = other_bills
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Member updated successfully!'})
            
            flash('Member updated successfully!', 'success')
            return redirect(url_for('members.view_member', member_id=member.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred while updating the member.'
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            flash(error_msg, 'error')
    
    return render_template('members/edit.html', member=member)

@members_bp.route('/<int:member_id>/delete', methods=['POST'])
@login_required
def delete_member(member_id):
    """Delete member"""
    from models import Member, Receipt
    from app import db
    
    member = Member.query.get_or_404(member_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != member.society_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
    elif current_user.role == 'superadmin':
        return jsonify({'success': False, 'message': 'Super admins cannot delete members directly'}), 403
    
    try:
        # Count receipts before deletion
        receipt_count = Receipt.query.filter_by(member_id=member.id).count()
        
        # Soft delete - mark as inactive
        member.is_active = False
        Receipt.query.filter_by(member_id=member.id).update({'is_active': False})
        
        db.session.commit()
        
        message = f'Member "{member.name}" and {receipt_count} associated receipts have been deleted.'
        
        if request.is_json:
            return jsonify({'success': True, 'message': message})
        
        flash(message, 'success')
        return redirect(url_for('members.list_members'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = 'An error occurred while deleting the member.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return redirect(url_for('members.view_member', member_id=member_id))

@members_bp.route('/api/search')
@login_required
def api_search_members():
    """API endpoint to search members"""
    from models import Member
    
    query = request.args.get('q', '').strip()
    society_id = request.args.get('society_id', type=int)
    
    if not query:
        return jsonify([])
    
    members_query = Member.query.filter_by(is_active=True).filter(
        Member.name.ilike(f'%{query}%')
    )
    
    # Filter by society based on user role
    if current_user.role == 'admin' and current_user.society_id:
        members_query = members_query.filter_by(society_id=current_user.society_id)
    elif society_id:
        members_query = members_query.filter_by(society_id=society_id)
    
    members = members_query.limit(10).all()
    
    return jsonify([{
        'id': member.id,
        'name': member.name,
        'building': member.building,
        'apartment': member.apartment,
        'phone': member.phone,
        'society_name': member.society.name if member.society else ''
    } for member in members])