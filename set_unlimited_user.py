#!/usr/bin/env python3
"""
Script to grant a user unlimited access.
Usage: python set_unlimited_user.py <username>
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('SECRET_KEY', 'dev-secret-key-for-testing-12345')
os.environ.setdefault('DATABASE_URL', 'sqlite:///composition.db')

from werkzeug.security import generate_password_hash
from app import app
from models import db, User, Subscription

def set_unlimited(username, email=None, password=None):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            if not email or not password:
                print(f"User '{username}' not found. Provide email and password to create.")
                return False
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_active=True
            )
            db.session.add(user)
            db.session.flush()
            print(f"✅ Created user '{username}'.")

        # Cancel any existing active subscriptions
        existing = Subscription.query.filter_by(user_id=user.id, status='active').all()
        for sub in existing:
            sub.status = 'canceled'

        # Create unlimited subscription with no expiry
        unlimited_sub = Subscription(
            user_id=user.id,
            plan_type='unlimited',
            status='active',
            amount=0,
            currency='USD',
            current_period_start=datetime.utcnow(),
            current_period_end=None  # No expiry
        )
        db.session.add(unlimited_sub)

        try:
            db.session.commit()
            print(f"✅ '{username}' now has unlimited access.")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False

if __name__ == '__main__':
    username = sys.argv[1] if len(sys.argv) > 1 else 'Eric'
    email = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else None
    set_unlimited(username, email, password)
