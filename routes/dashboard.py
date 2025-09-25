"""
Dashboard routes for Digital Society Management System
"""

from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard for society administrators"""
    if current_user.role != 'admin' or not current_user.society_id:
        return redirect(url_for('auth.login'))
    
    from models import Society, Member, Receipt
    
    # Get current user's society
    society = Society.query.get(current_user.society_id)
    if not society:
        flash('Society not found. Please contact support.', 'error')
        return redirect(url_for('auth.logout'))
    
    # Get statistics
    total_members = Member.query.filter_by(society_id=society.id, is_active=True).count()
    total_receipts = Receipt.query.filter_by(society_id=society.id, is_active=True).count()
    
    # Revenue statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_revenue = Receipt.query.filter_by(
        society_id=society.id,
        is_active=True
    ).filter(
        func.extract('month', Receipt.date) == current_month,
        func.extract('year', Receipt.date) == current_year
    ).with_entities(func.sum(Receipt.total_amount)).scalar() or 0
    
    total_revenue = Receipt.query.filter_by(
        society_id=society.id,
        is_active=True
    ).with_entities(func.sum(Receipt.total_amount)).scalar() or 0
    
    # Recent members (last 10)
    recent_members = Member.query.filter_by(
        society_id=society.id,
        is_active=True
    ).order_by(Member.created_at.desc()).limit(10).all()
    
    # Recent receipts (last 10)
    recent_receipts = Receipt.query.filter_by(
        society_id=society.id,
        is_active=True
    ).order_by(Receipt.date.desc()).limit(10).all()
    
    # Members with pending dues
    pending_dues_members = []
    members = Member.query.filter_by(society_id=society.id, is_active=True).all()
    
    for member in members:
        if member.dues_from_month and member.dues_from_year:
            due_date = datetime(member.dues_from_year, member.dues_from_month, 1)
            if due_date <= datetime.now():
                pending_dues_members.append(member)
    
    dashboard_data = {
        'society': society,
        'stats': {
            'total_members': total_members,
            'total_receipts': total_receipts,
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue,
            'pending_dues_count': len(pending_dues_members)
        },
        'recent_members': recent_members,
        'recent_receipts': recent_receipts,
        'pending_dues_members': pending_dues_members[:5]  # Show only first 5
    }
    
    return render_template('dashboard/admin.html', **dashboard_data)

@dashboard_bp.route('/superadmin')
@login_required
def superadmin_dashboard():
    """Super admin dashboard for system administrators"""
    if current_user.role != 'superadmin':
        return redirect(url_for('dashboard.admin_dashboard'))
    
    from models import Society, Member, Receipt, User
    
    # Get all statistics
    total_societies = Society.query.filter_by(is_active=True).count()
    total_members = Member.query.filter_by(is_active=True).count()
    total_receipts = Receipt.query.filter_by(is_active=True).count()
    total_users = User.query.filter_by(is_active=True).count()
    
    # Revenue statistics
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_revenue = Receipt.query.filter_by(is_active=True).filter(
        func.extract('month', Receipt.date) == current_month,
        func.extract('year', Receipt.date) == current_year
    ).with_entities(func.sum(Receipt.total_amount)).scalar() or 0
    
    total_revenue = Receipt.query.filter_by(is_active=True).with_entities(
        func.sum(Receipt.total_amount)
    ).scalar() or 0
    
    # Recent activities
    recent_societies = Society.query.filter_by(is_active=True).order_by(
        Society.created_at.desc()
    ).limit(5).all()
    
    recent_members = Member.query.filter_by(is_active=True).order_by(
        Member.created_at.desc()
    ).limit(10).all()
    
    recent_receipts = Receipt.query.filter_by(is_active=True).order_by(
        Receipt.date.desc()
    ).limit(10).all()
    
    # Society statistics
    society_stats = []
    societies = Society.query.filter_by(is_active=True).all()
    
    for society in societies:
        member_count = Member.query.filter_by(society_id=society.id, is_active=True).count()
        receipt_count = Receipt.query.filter_by(society_id=society.id, is_active=True).count()
        revenue = Receipt.query.filter_by(society_id=society.id, is_active=True).with_entities(
            func.sum(Receipt.total_amount)
        ).scalar() or 0
        
        society_stats.append({
            'society': society,
            'member_count': member_count,
            'receipt_count': receipt_count,
            'revenue': revenue
        })
    
    # Sort by revenue descending
    society_stats.sort(key=lambda x: x['revenue'], reverse=True)
    
    dashboard_data = {
        'stats': {
            'total_societies': total_societies,
            'total_members': total_members,
            'total_receipts': total_receipts,
            'total_users': total_users,
            'monthly_revenue': monthly_revenue,
            'total_revenue': total_revenue
        },
        'recent_societies': recent_societies,
        'recent_members': recent_members,
        'recent_receipts': recent_receipts,
        'society_stats': society_stats[:10]  # Top 10 societies
    }
    
    return render_template('dashboard/superadmin.html', **dashboard_data)

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    from models import Society, Member, Receipt
    
    if current_user.role == 'superadmin':
        # Super admin sees all data
        total_societies = Society.query.filter_by(is_active=True).count()
        total_members = Member.query.filter_by(is_active=True).count()
        total_receipts = Receipt.query.filter_by(is_active=True).count()
        total_revenue = Receipt.query.filter_by(is_active=True).with_entities(
            func.sum(Receipt.total_amount)
        ).scalar() or 0
        
        return jsonify({
            'total_societies': total_societies,
            'total_members': total_members,
            'total_receipts': total_receipts,
            'total_revenue': total_revenue
        })
    
    elif current_user.role == 'admin' and current_user.society_id:
        # Admin sees only their society data
        society_id = current_user.society_id
        total_members = Member.query.filter_by(society_id=society_id, is_active=True).count()
        total_receipts = Receipt.query.filter_by(society_id=society_id, is_active=True).count()
        total_revenue = Receipt.query.filter_by(society_id=society_id, is_active=True).with_entities(
            func.sum(Receipt.total_amount)
        ).scalar() or 0
        
        return jsonify({
            'total_members': total_members,
            'total_receipts': total_receipts,
            'total_revenue': total_revenue
        })
    
    return jsonify({'error': 'Unauthorized'}), 403

@dashboard_bp.route('/api/revenue-chart')
@login_required
def api_revenue_chart():
    """API endpoint for revenue chart data"""
    from models import Receipt
    
    # Get last 12 months of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    query = Receipt.query.filter_by(is_active=True).filter(Receipt.date >= start_date)
    
    if current_user.role == 'admin' and current_user.society_id:
        query = query.filter_by(society_id=current_user.society_id)
    
    receipts = query.all()
    
    # Group by month
    monthly_data = {}
    for receipt in receipts:
        month_key = receipt.date.strftime('%Y-%m')
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += receipt.total_amount
    
    # Prepare chart data
    chart_data = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        chart_data.append({
            'month': current_date.strftime('%b %Y'),
            'revenue': monthly_data.get(month_key, 0)
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return jsonify(chart_data)