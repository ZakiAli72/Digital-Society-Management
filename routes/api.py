"""
API routes for Digital Society Management System
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard-stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics"""
    from models import Society, Member, Receipt
    from sqlalchemy import func
    
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
            'total_revenue': float(total_revenue)
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
            'total_revenue': float(total_revenue)
        })
    
    return jsonify({'error': 'Unauthorized'}), 403

@api_bp.route('/revenue-chart')
@login_required
def revenue_chart():
    """Get revenue chart data for the last 12 months"""
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
            'revenue': float(monthly_data.get(month_key, 0))
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return jsonify(chart_data)

@api_bp.route('/members/search')
@login_required
def search_members():
    """Search members by name"""
    from models import Member
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    members_query = Member.query.filter_by(is_active=True).filter(
        Member.name.ilike(f'%{query}%')
    )
    
    # Filter by society based on user role
    if current_user.role == 'admin' and current_user.society_id:
        members_query = members_query.filter_by(society_id=current_user.society_id)
    
    members = members_query.limit(10).all()
    
    return jsonify([{
        'id': member.id,
        'name': member.name,
        'building': member.building,
        'apartment': member.apartment,
        'phone': member.phone,
        'society_name': member.society.name if member.society else ''
    } for member in members])

@api_bp.route('/societies/search')
@login_required
def search_societies():
    """Search societies by name (superadmin only)"""
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

@api_bp.route('/receipts/search')
@login_required
def search_receipts():
    """Search receipts by receipt number or member name"""
    from models import Receipt
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    receipts_query = Receipt.query.filter_by(is_active=True)
    
    # Filter by society based on user role
    if current_user.role == 'admin' and current_user.society_id:
        receipts_query = receipts_query.filter_by(society_id=current_user.society_id)
    
    # Search by receipt number or member name
    try:
        receipt_number = int(query)
        receipts_query = receipts_query.filter(Receipt.receipt_number == receipt_number)
    except ValueError:
        receipts_query = receipts_query.join(Receipt.member).filter(
            Receipt.member.has(Member.name.ilike(f'%{query}%'))
        )
    
    receipts = receipts_query.limit(10).all()
    
    return jsonify([{
        'id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'member_name': receipt.member.name if receipt.member else '',
        'total_amount': float(receipt.total_amount),
        'date': receipt.date.isoformat(),
        'society_name': receipt.society.name if receipt.society else ''
    } for receipt in receipts])

@api_bp.route('/member/<int:member_id>/details')
@login_required
def member_details(member_id):
    """Get detailed member information for receipt generation"""
    from models import Member
    
    member = Member.query.get_or_404(member_id)
    
    # Check permissions
    if current_user.role == 'admin':
        if current_user.society_id != member.society_id:
            return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': member.id,
        'name': member.name,
        'building': member.building,
        'apartment': member.apartment,
        'monthly_maintenance': float(member.monthly_maintenance),
        'monthly_water_bill': float(member.monthly_water_bill),
        'other_bills': member.other_bills_list,
        'dues_from_month': member.dues_from_month,
        'dues_from_year': member.dues_from_year
    })

@api_bp.route('/receipt/<int:receipt_id>/duplicate-check')
@login_required
def check_receipt_duplicate(receipt_id):
    """Check if a receipt period would create a duplicate"""
    from models import Receipt
    
    member_id = request.args.get('member_id', type=int)
    from_month = request.args.get('from_month', type=int)
    from_year = request.args.get('from_year', type=int)
    till_month = request.args.get('till_month', type=int)
    till_year = request.args.get('till_year', type=int)
    
    if not all([member_id, from_month, from_year, till_month, till_year]):
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Get existing receipts for the member
    existing_receipts = Receipt.query.filter_by(
        member_id=member_id,
        is_active=True
    ).filter(Receipt.id != receipt_id).all()  # Exclude current receipt if editing
    
    new_from_period = from_year * 12 + from_month
    new_till_period = till_year * 12 + till_month
    
    for receipt in existing_receipts:
        existing_from_period = receipt.payment_from_year * 12 + receipt.payment_from_month
        existing_till_period = receipt.payment_till_year * 12 + receipt.payment_till_month
        
        # Check if periods overlap
        if max(new_from_period, existing_from_period) <= min(new_till_period, existing_till_period):
            return jsonify({
                'duplicate': True,
                'conflicting_receipt': {
                    'id': receipt.id,
                    'receipt_number': receipt.receipt_number,
                    'from_month': receipt.payment_from_month,
                    'from_year': receipt.payment_from_year,
                    'till_month': receipt.payment_till_month,
                    'till_year': receipt.payment_till_year
                }
            })
    
    return jsonify({'duplicate': False})

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0'
    })