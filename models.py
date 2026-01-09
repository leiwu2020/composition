from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def get_active_subscription(self):
        """Get the active subscription if any"""
        return Subscription.query.filter_by(
            user_id=self.id,
            status='active'
        ).order_by(Subscription.created_at.desc()).first()
    
    def has_active_subscription(self):
        """Check if user has an active subscription"""
        subscription = self.get_active_subscription()
        if subscription:
            return subscription.is_active()
        return False

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='inactive')  # active, canceled, past_due, etc.
    plan_type = db.Column(db.String(50), default='monthly')  # monthly, yearly
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status == 'active':
            if self.current_period_end:
                return datetime.utcnow() < self.current_period_end
            return True
        return False
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        if self.current_period_end and self.is_active():
            remaining = self.current_period_end - datetime.utcnow()
            return max(0, remaining.days)
        return 0

