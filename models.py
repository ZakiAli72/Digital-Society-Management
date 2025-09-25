"""
Database Models for Digital Society Management System
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import uuid

# This will be set from app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # 'admin' or 'superadmin'
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    society = db.relationship('Society', back_populates='admin_users')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'society_id': self.society_id,
            'society_name': self.society.name if self.society else None,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.email}>'

class Society(db.Model):
    """Society model for housing societies/complexes"""
    __tablename__ = 'societies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=True)
    registration_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    registration_year = db.Column(db.Integer, nullable=False)
    signature_authority = db.Column(db.String(200), nullable=True)
    signature_type = db.Column(db.String(20), default='text')  # 'text' or 'image'
    signature_text = db.Column(db.String(200), nullable=True)
    signature_image = db.Column(db.Text, nullable=True)  # base64 encoded image
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    admin_users = db.relationship('User', back_populates='society')
    members = db.relationship('Member', back_populates='society', cascade='all, delete-orphan')
    receipts = db.relationship('Receipt', back_populates='society', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert society to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'registration_number': self.registration_number,
            'registration_year': self.registration_year,
            'signature_authority': self.signature_authority,
            'signature_type': self.signature_type,
            'signature_text': self.signature_text,
            'signature_image': self.signature_image,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'member_count': len(self.members),
            'receipt_count': len(self.receipts)
        }
    
    def __repr__(self):
        return f'<Society {self.name}>'

class Member(db.Model):
    """Member model for society residents"""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country_code = db.Column(db.String(10), nullable=False, default='+1')
    phone = db.Column(db.String(20), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    apartment = db.Column(db.String(50), nullable=False)
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=False)
    monthly_maintenance = db.Column(db.Float, default=0.0)
    monthly_water_bill = db.Column(db.Float, default=0.0)
    other_bills = db.Column(db.Text, nullable=True)  # JSON string for additional bills
    dues_from_month = db.Column(db.Integer, nullable=True)  # 1-12
    dues_from_year = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    society = db.relationship('Society', back_populates='members')
    receipts = db.relationship('Receipt', back_populates='member', cascade='all, delete-orphan')
    
    @property
    def other_bills_list(self):
        """Get other bills as list of dictionaries"""
        if self.other_bills:
            try:
                return json.loads(self.other_bills)
            except:
                return []
        return []
    
    @other_bills_list.setter
    def other_bills_list(self, value):
        """Set other bills from list of dictionaries"""
        self.other_bills = json.dumps(value) if value else None
    
    def to_dict(self):
        """Convert member to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'country_code': self.country_code,
            'phone': self.phone,
            'building': self.building,
            'apartment': self.apartment,
            'society_id': self.society_id,
            'society_name': self.society.name if self.society else None,
            'monthly_maintenance': self.monthly_maintenance,
            'monthly_water_bill': self.monthly_water_bill,
            'other_bills': self.other_bills_list,
            'dues_from_month': self.dues_from_month,
            'dues_from_year': self.dues_from_year,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'receipt_count': len(self.receipts)
        }
    
    def __repr__(self):
        return f'<Member {self.name}>'

class Receipt(db.Model):
    """Receipt model for payment receipts"""
    __tablename__ = 'receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    society_id = db.Column(db.Integer, db.ForeignKey('societies.id'), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string for payment items
    total_amount = db.Column(db.Float, nullable=False)
    payment_from_month = db.Column(db.Integer, nullable=False)  # 1-12
    payment_from_year = db.Column(db.Integer, nullable=False)
    payment_till_month = db.Column(db.Integer, nullable=False)  # 1-12
    payment_till_year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    member = db.relationship('Member', back_populates='receipts')
    society = db.relationship('Society', back_populates='receipts')
    
    # Composite unique constraint for receipt number per society
    __table_args__ = (db.UniqueConstraint('society_id', 'receipt_number', name='unique_society_receipt_number'),)
    
    @property
    def items_list(self):
        """Get items as list of dictionaries"""
        if self.items:
            try:
                return json.loads(self.items)
            except:
                return []
        return []
    
    @items_list.setter
    def items_list(self, value):
        """Set items from list of dictionaries"""
        self.items = json.dumps(value) if value else None
    
    def to_dict(self):
        """Convert receipt to dictionary"""
        return {
            'id': self.id,
            'receipt_number': self.receipt_number,
            'date': self.date.isoformat(),
            'member_id': self.member_id,
            'member_name': self.member.name if self.member else None,
            'society_id': self.society_id,
            'society_name': self.society.name if self.society else None,
            'items': self.items_list,
            'total_amount': self.total_amount,
            'payment_from_month': self.payment_from_month,
            'payment_from_year': self.payment_from_year,
            'payment_till_month': self.payment_till_month,
            'payment_till_year': self.payment_till_year,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<Receipt #{self.receipt_number}>'

class Backup(db.Model):
    """Backup model for system data backups"""
    __tablename__ = 'backups'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    backup_type = db.Column(db.String(50), default='manual')  # 'manual' or 'automatic'
    file_size = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    creator = db.relationship('User')
    
    def to_dict(self):
        """Convert backup to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'creator_email': self.creator.email if self.creator else None,
            'backup_type': self.backup_type,
            'file_size': self.file_size,
            'description': self.description,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<Backup {self.filename}>'