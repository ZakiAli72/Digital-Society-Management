"""
Receipt management routes for Digital Society Management System
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from datetime import datetime
import json

receipts_bp = Blueprint('receipts', __name__)

@receipts_bp.route('/')
@login_required
def list_receipts():
    """List receipts"""
    from models import Receipt, Society
    
    if current_user.role == 'superadmin':
        # Super admin sees all receipts
        page = request.args.get('page', 1, type=int)
        society_id = request.args.get('society_id', type=int)
        search = request.args.get('search', '').strip()
        
        query = Receipt.query.filter_by(is_active=True)
        
        if society_id:
            query = query.filter_by(society_id=society_id)
        
        if search:
            query = query.join(Receipt.member).filter(
                Receipt.member.has(name=search) | 
                Receipt.receipt_number.like(f'%{search}%')
            )
        
        receipts = query.order_by(Receipt.date.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        societies = Society.query.filter_by(is_active=True).all()
        
    elif current_user.role == 'admin' and current_user.society_id:
        # Admin sees only their society receipts
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        query = Receipt.query.filter_by(society_id=current_user.society_id, is_active=True)
        
        if search:
            query = query.join(Receipt.member).filter(
                Receipt.member.has(name=search) | 
                Receipt.receipt_number.like(f'%{search}%')
            )
        
        receipts = query.order_by(Receipt.date.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        societies = [Society.query.get(current_user.society_id)]
        
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    return render_template('receipts/list.html', 
                         receipts=receipts, 
                         societies=societies,
                         selected_society_id=request.args.get('society_id', type=int),
                         search_query=request.args.get('search', ''))

@receipts_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_receipt():
    """Generate new receipt"""
    if current_user.role == 'superadmin':
        flash('Super admins cannot generate receipts directly. Please use a society admin account.', 'error')
        return redirect(url_for('receipts.list_receipts'))
    
    if not current_user.society_id:
        flash('No society associated with your account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Member, Receipt, Society
    from app import db
    
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    members = Member.query.filter_by(society_id=society.id, is_active=True).order_by(Member.name).all()
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        member_id = data.get('member_id')
        payment_from_month = data.get('payment_from_month')
        payment_from_year = data.get('payment_from_year')
        payment_till_month = data.get('payment_till_month')
        payment_till_year = data.get('payment_till_year')
        description = data.get('description', '').strip()
        
        # Validation
        errors = []
        
        if not member_id:
            errors.append('Please select a member')
        else:
            member = Member.query.get(member_id)
            if not member or member.society_id != society.id:
                errors.append('Invalid member selected')
        
        try:
            payment_from_month = int(payment_from_month)
            payment_from_year = int(payment_from_year)
            payment_till_month = int(payment_till_month)
            payment_till_year = int(payment_till_year)
            
            if payment_from_month < 1 or payment_from_month > 12:
                errors.append('Invalid payment from month')
            if payment_till_month < 1 or payment_till_month > 12:
                errors.append('Invalid payment till month')
            if payment_from_year < 2020 or payment_from_year > 2030:
                errors.append('Invalid payment from year')
            if payment_till_year < 2020 or payment_till_year > 2030:
                errors.append('Invalid payment till year')
            
            # Check if from date is before till date
            from_date = datetime(payment_from_year, payment_from_month, 1)
            till_date = datetime(payment_till_year, payment_till_month, 1)
            if from_date > till_date:
                errors.append('Payment from date must be before payment till date')
                
        except (ValueError, TypeError):
            errors.append('Invalid payment dates')
        
        if not errors and member:
            # Check for overlapping receipts
            existing_receipts = Receipt.query.filter_by(
                member_id=member.id, 
                is_active=True
            ).all()
            
            new_from_period = payment_from_year * 12 + payment_from_month
            new_till_period = payment_till_year * 12 + payment_till_month
            
            for receipt in existing_receipts:
                existing_from_period = receipt.payment_from_year * 12 + receipt.payment_from_month
                existing_till_period = receipt.payment_till_year * 12 + receipt.payment_till_month
                
                # Check if periods overlap
                if max(new_from_period, existing_from_period) <= min(new_till_period, existing_till_period):
                    errors.append(f'Receipt period overlaps with existing receipt #{receipt.receipt_number:04d}')
                    break
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors})
            for error in errors:
                flash(error, 'error')
            return render_template('receipts/generate.html', society=society, members=members)
        
        try:
            # Calculate months and items
            months = (till_date.year - from_date.year) * 12 + (till_date.month - from_date.month) + 1
            
            items = []
            total_amount = 0
            
            if member.monthly_maintenance > 0:
                amount = member.monthly_maintenance * months
                items.append({
                    'description': f'Maintenance Bill ({months} month{"s" if months > 1 else ""})',
                    'amount': amount
                })
                total_amount += amount
            
            if member.monthly_water_bill > 0:
                amount = member.monthly_water_bill * months
                items.append({
                    'description': f'Water Bill ({months} month{"s" if months > 1 else ""})',
                    'amount': amount
                })
                total_amount += amount
            
            # Add other bills
            for bill in member.other_bills_list:
                if bill.get('amount', 0) > 0:
                    amount = bill['amount'] * months
                    items.append({
                        'description': f'{bill["name"]} ({months} month{"s" if months > 1 else ""})',
                        'amount': amount
                    })
                    total_amount += amount
            
            if total_amount <= 0:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'No charges found for this member'})
                flash('No charges found for this member', 'error')
                return render_template('receipts/generate.html', society=society, members=members)
            
            # Get next receipt number for this society
            last_receipt = Receipt.query.filter_by(
                society_id=society.id
            ).order_by(Receipt.receipt_number.desc()).first()
            
            next_receipt_number = (last_receipt.receipt_number + 1) if last_receipt else 1
            
            # Create receipt
            receipt = Receipt(
                receipt_number=next_receipt_number,
                member_id=member.id,
                society_id=society.id,
                total_amount=total_amount,
                payment_from_month=payment_from_month,
                payment_from_year=payment_from_year,
                payment_till_month=payment_till_month,
                payment_till_year=payment_till_year,
                description=description if description else None
            )
            
            receipt.items_list = items
            
            db.session.add(receipt)
            
            # Update member dues
            next_due_date = datetime(payment_till_year, payment_till_month, 1)
            if next_due_date.month == 12:
                next_due_date = next_due_date.replace(year=next_due_date.year + 1, month=1)
            else:
                next_due_date = next_due_date.replace(month=next_due_date.month + 1)
            
            member.dues_from_month = next_due_date.month
            member.dues_from_year = next_due_date.year
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Receipt generated successfully!',
                    'receipt_id': receipt.id,
                    'receipt_number': receipt.receipt_number
                })
            
            flash(f'Receipt #{receipt.receipt_number:04d} generated successfully!', 'success')
            return redirect(url_for('receipts.view_receipt', receipt_id=receipt.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred while generating the receipt.'
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            flash(error_msg, 'error')
    
    return render_template('receipts/generate.html', society=society, members=members)

@receipts_bp.route('/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    """View receipt details"""
    from models import Receipt
    
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != receipt.society_id:
            flash('Access denied.', 'error')
            return redirect(url_for('receipts.list_receipts'))
    
    return render_template('receipts/view.html', receipt=receipt)

@receipts_bp.route('/<int:receipt_id>/print')
@login_required
def print_receipt(receipt_id):
    """Print receipt (print-friendly version)"""
    from models import Receipt
    
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != receipt.society_id:
            flash('Access denied.', 'error')
            return redirect(url_for('receipts.list_receipts'))
    
    return render_template('receipts/print.html', receipt=receipt)

@receipts_bp.route('/<int:receipt_id>/delete', methods=['POST'])
@login_required
def delete_receipt(receipt_id):
    """Delete receipt"""
    from models import Receipt, Member
    from app import db
    
    receipt = Receipt.query.get_or_404(receipt_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != receipt.society_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
    elif current_user.role == 'superadmin':
        return jsonify({'success': False, 'message': 'Super admins cannot delete receipts directly'}), 403
    
    try:
        # Revert member dues
        member = receipt.member
        if member:
            member.dues_from_month = receipt.payment_from_month
            member.dues_from_year = receipt.payment_from_year
        
        # Soft delete - mark as inactive
        receipt.is_active = False
        
        db.session.commit()
        
        message = f'Receipt #{receipt.receipt_number:04d} has been deleted and member dues updated.'
        
        if request.is_json:
            return jsonify({'success': True, 'message': message})
        
        flash(message, 'success')
        return redirect(url_for('receipts.list_receipts'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = 'An error occurred while deleting the receipt.'
        
        if request.is_json:
            return jsonify({'success': False, 'message': error_msg})
        
        flash(error_msg, 'error')
        return redirect(url_for('receipts.view_receipt', receipt_id=receipt_id))

@receipts_bp.route('/bulk-generate', methods=['GET', 'POST'])
@login_required
def bulk_generate():
    """Bulk receipt generation"""
    if current_user.role == 'superadmin':
        flash('Super admins cannot generate receipts directly. Please use a society admin account.', 'error')
        return redirect(url_for('receipts.list_receipts'))
    
    if not current_user.society_id:
        flash('No society associated with your account.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Member, Receipt, Society
    from app import db
    
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found.', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))
    
    members = Member.query.filter_by(society_id=society.id, is_active=True).order_by(Member.name).all()
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        member_periods = data.get('member_periods', [])
        description = data.get('description', '').strip()
        
        if not member_periods:
            if request.is_json:
                return jsonify({'success': False, 'message': 'No members selected'})
            flash('No members selected', 'error')
            return render_template('receipts/bulk_generate.html', society=society, members=members)
        
        try:
            generated_count = 0
            skipped_count = 0
            errors = []
            
            # Get next receipt number
            last_receipt = Receipt.query.filter_by(
                society_id=society.id
            ).order_by(Receipt.receipt_number.desc()).first()
            
            next_receipt_number = (last_receipt.receipt_number + 1) if last_receipt else 1
            
            for member_period in member_periods:
                member_id = member_period.get('member_id')
                payment_from_month = int(member_period.get('payment_from_month'))
                payment_from_year = int(member_period.get('payment_from_year'))
                payment_till_month = int(member_period.get('payment_till_month'))
                payment_till_year = int(member_period.get('payment_till_year'))
                
                member = Member.query.get(member_id)
                if not member or member.society_id != society.id:
                    continue
                
                # Check for overlapping receipts
                existing_receipts = Receipt.query.filter_by(
                    member_id=member.id, 
                    is_active=True
                ).all()
                
                new_from_period = payment_from_year * 12 + payment_from_month
                new_till_period = payment_till_year * 12 + payment_till_month
                
                has_overlap = False
                for receipt in existing_receipts:
                    existing_from_period = receipt.payment_from_year * 12 + receipt.payment_from_month
                    existing_till_period = receipt.payment_till_year * 12 + receipt.payment_till_month
                    
                    if max(new_from_period, existing_from_period) <= min(new_till_period, existing_till_period):
                        has_overlap = True
                        break
                
                if has_overlap:
                    skipped_count += 1
                    continue
                
                # Calculate receipt details
                from_date = datetime(payment_from_year, payment_from_month, 1)
                till_date = datetime(payment_till_year, payment_till_month, 1)
                months = (till_date.year - from_date.year) * 12 + (till_date.month - from_date.month) + 1
                
                items = []
                total_amount = 0
                
                if member.monthly_maintenance > 0:
                    amount = member.monthly_maintenance * months
                    items.append({
                        'description': f'Maintenance Bill ({months} month{"s" if months > 1 else ""})',
                        'amount': amount
                    })
                    total_amount += amount
                
                if member.monthly_water_bill > 0:
                    amount = member.monthly_water_bill * months
                    items.append({
                        'description': f'Water Bill ({months} month{"s" if months > 1 else ""})',
                        'amount': amount
                    })
                    total_amount += amount
                
                for bill in member.other_bills_list:
                    if bill.get('amount', 0) > 0:
                        amount = bill['amount'] * months
                        items.append({
                            'description': f'{bill["name"]} ({months} month{"s" if months > 1 else ""})',
                            'amount': amount
                        })
                        total_amount += amount
                
                if total_amount <= 0:
                    skipped_count += 1
                    continue
                
                # Create receipt
                receipt = Receipt(
                    receipt_number=next_receipt_number,
                    member_id=member.id,
                    society_id=society.id,
                    total_amount=total_amount,
                    payment_from_month=payment_from_month,
                    payment_from_year=payment_from_year,
                    payment_till_month=payment_till_month,
                    payment_till_year=payment_till_year,
                    description=description if description else None
                )
                
                receipt.items_list = items
                db.session.add(receipt)
                
                # Update member dues
                next_due_date = datetime(payment_till_year, payment_till_month, 1)
                if next_due_date.month == 12:
                    next_due_date = next_due_date.replace(year=next_due_date.year + 1, month=1)
                else:
                    next_due_date = next_due_date.replace(month=next_due_date.month + 1)
                
                member.dues_from_month = next_due_date.month
                member.dues_from_year = next_due_date.year
                
                next_receipt_number += 1
                generated_count += 1
            
            db.session.commit()
            
            message = f'{generated_count} receipt(s) generated successfully!'
            if skipped_count > 0:
                message += f' {skipped_count} member(s) skipped due to overlapping periods or no charges.'
            
            if request.is_json:
                return jsonify({'success': True, 'message': message})
            
            flash(message, 'success')
            return redirect(url_for('receipts.list_receipts'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'An error occurred during bulk receipt generation.'
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            
            flash(error_msg, 'error')
    
    return render_template('receipts/bulk_generate.html', society=society, members=members)