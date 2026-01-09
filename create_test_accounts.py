#!/usr/bin/env python3
"""
Script to create test accounts with different subscription plans
"""
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ['SECRET_KEY'] = 'dev-secret-key-for-testing-12345'
os.environ['DATABASE_URL'] = 'sqlite:///composition.db'

from app import app
from models import db, User, Subscription, PLANS

def create_test_accounts():
    """Create test accounts with subscriptions"""
    with app.app_context():
        # Test accounts configuration
        test_accounts = [
            {
                'username': 'TestA',
                'email': 'testa@example.com',
                'password': 'test123',
                'plan': 'free'
            },
            {
                'username': 'TestB',
                'email': 'testb@example.com',
                'password': 'test123',
                'plan': 'basic'
            },
            {
                'username': 'TestC',
                'email': 'testc@example.com',
                'password': 'test123',
                'plan': 'elite'
            },
            {
                'username': 'TestD',
                'email': 'testd@example.com',
                'password': 'test123',
                'plan': 'advanced'
            },
            {
                'username': 'TestE',
                'email': 'teste@example.com',
                'password': 'test123',
                'plan': 'annual'
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for account in test_accounts:
            # Check if user exists
            user = User.query.filter_by(username=account['username']).first()
            
            if not user:
                # Create new user
                user = User(
                    username=account['username'],
                    email=account['email'],
                    password_hash=generate_password_hash(account['password']),
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()  # Get user ID
                created_count += 1
                print(f"✅ Created user: {account['username']}")
            else:
                print(f"ℹ️  User already exists: {account['username']}")
            
            # Check if subscription exists
            subscription = Subscription.query.filter_by(
                user_id=user.id,
                plan_type=account['plan']
            ).first()
            
            if not subscription:
                # Create subscription
                plan = PLANS[account['plan']]
                now = datetime.utcnow()
                
                if account['plan'] == 'annual':
                    period_end = now + timedelta(days=365)
                else:
                    period_end = now + timedelta(days=30)
                
                subscription = Subscription(
                    user_id=user.id,
                    plan_type=account['plan'],
                    status='active',
                    amount=plan['price'],
                    currency='USD',
                    current_period_start=now,
                    current_period_end=period_end
                )
                db.session.add(subscription)
                updated_count += 1
                print(f"  ✅ Created {account['plan']} subscription")
            else:
                # Update existing subscription to active
                subscription.status = 'active'
                if not subscription.current_period_end:
                    if account['plan'] == 'annual':
                        subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
                    else:
                        subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                print(f"  ✅ Updated subscription to {account['plan']}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully created/updated accounts!")
            print(f"   - New users: {created_count}")
            print(f"   - New/updated subscriptions: {updated_count}")
            print("\nTest accounts:")
            print("  TestA - Free plan (3 queries/month)")
            print("  TestB - Basic plan (3 queries/week) - $4.99/month")
            print("  TestC - Elite plan (10 queries/day) - $9.99/month")
            print("  TestD - Advanced plan (100 queries/month) - $19.99/month")
            print("  TestE - Annual Pass (100 queries/month) - $199.99/year")
            print("\nAll accounts use password: test123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("Creating test accounts with subscriptions...\n")
    create_test_accounts()

