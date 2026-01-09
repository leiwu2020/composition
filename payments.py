from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, User, Subscription, PLANS
from datetime import datetime, timedelta
from dotenv import load_dotenv
import stripe
import os

# Load environment variables first
load_dotenv()

payments_bp = Blueprint('payments', __name__)

# Initialize Stripe - load key from environment
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
else:
    print("WARNING: STRIPE_SECRET_KEY not found in environment variables!")

# Plan prices (in cents) - moved to models.py but keeping here for backward compatibility
try:
    from models import PLAN_PRICES
except ImportError:
    PLAN_PRICES = {
        'free': 0,
        'basic': 499,  # $4.99
        'elite': 999,  # $9.99
        'advanced': 1999,  # $19.99
        'annual': 19999  # $199.99
    }

@payments_bp.route('/pricing')
def pricing():
    """Display pricing page"""
    # Get user's current plan if logged in
    current_plan_type = 'free'
    if current_user.is_authenticated:
        # Force complete refresh - expire all caches
        from sqlalchemy.orm import object_session
        session = object_session(current_user)
        if session:
            # Expire all cached data
            session.expire_all()
        
        # Get completely fresh user from database (bypassing cache)
        fresh_user = db.session.query(User).filter_by(id=current_user.id).first()
        
        # Force expire again to ensure fresh query
        if session:
            session.expire(fresh_user)
            session.expire_all()
        
        # Debug: Check all subscriptions first
        all_subs = db.session.query(Subscription).filter_by(user_id=fresh_user.id).all()
        print(f"Pricing page - User: {fresh_user.username} (ID: {fresh_user.id})")
        print(f"  All subscriptions in DB: {len(all_subs)}")
        for sub in all_subs:
            print(f"    - ID: {sub.id}, Plan: {sub.plan_type}, Status: {sub.status}, Updated: {sub.updated_at}, User ID: {sub.user_id}")
        
        active_subs = db.session.query(Subscription).filter(
            Subscription.user_id == fresh_user.id,
            Subscription.status == 'active'
        ).all()
        print(f"  Active subscriptions: {len(active_subs)}")
        for sub in active_subs:
            print(f"    - ID: {sub.id}, Plan: {sub.plan_type}, Status: {sub.status}")
        
        # Now get the plan - this should query fresh from DB
        current_plan_type = fresh_user.get_plan()
        
        # Debug: verify what we got
        active_sub = fresh_user.get_active_subscription()
        print(f"  Current plan (get_plan): {current_plan_type}")
        if active_sub:
            print(f"  get_active_subscription() returned: ID={active_sub.id}, Plan={active_sub.plan_type}, Status={active_sub.status}")
        else:
            print(f"  get_active_subscription() returned: None")
    
    return render_template('pricing.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
                         plans=PLANS,
                         current_plan_type=current_plan_type)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        # Verify Stripe API key is set
        if not stripe.api_key:
            # Try to reload from environment
            load_dotenv()
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            if not stripe.api_key:
                return jsonify({
                    'error': 'Stripe API key not configured. Please contact support.',
                    'success': False
                }), 500
        
        plan_type = request.json.get('plan_type', 'basic')
        
        if plan_type == 'free':
            # Free plan doesn't need payment
            return jsonify({'error': 'Free plan does not require payment', 'success': False}), 400
        
        if plan_type not in PLANS:
            return jsonify({'error': 'Invalid plan type', 'success': False}), 400
        
        plan = PLANS[plan_type]
        price_cents = PLAN_PRICES.get(plan_type, 0)
        
        if price_cents == 0:
            return jsonify({'error': 'This plan does not require payment', 'success': False}), 400
        
        # Create or retrieve Stripe customer
        customer_id = None
        if current_user.subscriptions:
            existing_sub = Subscription.query.filter(
                Subscription.user_id == current_user.id,
                Subscription.stripe_customer_id.isnot(None)
            ).first()
            if existing_sub:
                customer_id = existing_sub.stripe_customer_id
        
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': str(current_user.id), 'username': current_user.username}
            )
            customer_id = customer.id
        
        # Determine interval
        interval = 'month' if plan['interval'] == 'month' else 'year'
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'AI Article Generator - {plan["name"]} Plan',
                        'description': get_plan_description(plan_type)
                    },
                    'recurring': {
                        'interval': interval
                    },
                    'unit_amount': price_cents,
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'payment/cancel',
            metadata={'user_id': str(current_user.id), 'plan_type': plan_type}
        )
        
        return jsonify({
            'success': True,
            'sessionId': checkout_session.id,
            'url': checkout_session.url
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

def get_plan_description(plan_type):
    """Get description for plan"""
    plan = PLANS.get(plan_type, {})
    if plan.get('queries_per_day'):
        return f'{plan["queries_per_day"]} queries per day'
    elif plan.get('queries_per_week'):
        return f'{plan["queries_per_week"]} queries per week'
    elif plan.get('queries_per_month'):
        return f'{plan["queries_per_month"]} queries per month'
    return 'Unlimited queries'

@payments_bp.route('/success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Invalid payment session', 'error')
        return redirect(url_for('payments.pricing'))
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify it belongs to current user
        if session.metadata.get('user_id') != str(current_user.id):
            flash('Invalid payment session', 'error')
            return redirect(url_for('payments.pricing'))
        
        # Retrieve the subscription
        subscription_id = session.subscription
        if not subscription_id:
            flash('Invalid payment session - no subscription found', 'error')
            return redirect(url_for('payments.pricing'))
        
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Get plan type from metadata
        plan_type = session.metadata.get('plan_type', 'basic')
        is_plan_change = session.metadata.get('is_plan_change', 'false') == 'true'
        
        # Safely get subscription items
        if not hasattr(stripe_subscription, 'items') or not stripe_subscription.items:
            flash('Invalid subscription data', 'error')
            return redirect(url_for('payments.pricing'))
        
        # Handle both dict and object access for items
        if isinstance(stripe_subscription.items, dict):
            items_data = stripe_subscription.items.get('data', [])
        else:
            # It's a Stripe object with data attribute
            items_data = stripe_subscription.items.data if hasattr(stripe_subscription.items, 'data') else []
        
        if not items_data or len(items_data) == 0:
            flash('Invalid subscription - no items found', 'error')
            return redirect(url_for('payments.pricing'))
        
        # Get price from first item
        first_item = items_data[0]
        if isinstance(first_item, dict):
            price_data = first_item.get('price', {})
            unit_amount = price_data.get('unit_amount', 0) if isinstance(price_data, dict) else (first_item.get('price', {}).get('unit_amount', 0) if hasattr(first_item.get('price', {}), 'unit_amount') else 0)
        else:
            # It's a Stripe object
            price_obj = first_item.price if hasattr(first_item, 'price') else None
            unit_amount = price_obj.unit_amount if price_obj and hasattr(price_obj, 'unit_amount') else 0
        
        # CRITICAL: ALWAYS cancel ALL existing active subscriptions before creating/updating new one
        # This ensures the new paid subscription is the only active one
        # (Otherwise, old free subscriptions will still be active and get picked up)
        old_subscriptions = Subscription.query.filter(
            Subscription.user_id == current_user.id,
            Subscription.status == 'active',
            Subscription.stripe_subscription_id != subscription_id
        ).all()
        
        print(f"Found {len(old_subscriptions)} existing active subscriptions to cancel")
        for old_sub in old_subscriptions:
            if old_sub.stripe_subscription_id:
                try:
                    stripe.Subscription.modify(
                        old_sub.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                except Exception as e:
                    print(f"Error canceling old subscription in Stripe: {e}")
            # Mark old subscription as canceled
            old_sub.status = 'canceled'
            old_sub.updated_at = datetime.utcnow()
            print(f"Cancelled old subscription: Plan={old_sub.plan_type}, ID={old_sub.id}, Stripe ID={old_sub.stripe_subscription_id}")
        
        # Create or update subscription in database
        # Use fresh query to bypass cache
        subscription = db.session.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            # New subscription - create it
            subscription = Subscription(
                user_id=current_user.id,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=stripe_subscription.customer if hasattr(stripe_subscription, 'customer') else None,
                status='active',  # Set to active explicitly
                plan_type=plan_type,  # Use plan_type from metadata
                amount=unit_amount / 100,
                currency=(stripe_subscription.currency.upper() if hasattr(stripe_subscription, 'currency') else 'USD'),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start) if hasattr(stripe_subscription, 'current_period_start') else datetime.utcnow(),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end) if hasattr(stripe_subscription, 'current_period_end') else datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(subscription)
            print(f"Payment success - Created NEW subscription: Plan={plan_type}, User={current_user.username}, User ID={current_user.id}")
        else:
            # Update existing subscription
            subscription.status = 'active'  # Ensure it's active
            subscription.plan_type = plan_type  # Update plan type from metadata
            subscription.stripe_customer_id = stripe_subscription.customer if hasattr(stripe_subscription, 'customer') else subscription.stripe_customer_id
            subscription.amount = unit_amount / 100
            subscription.currency = (stripe_subscription.currency.upper() if hasattr(stripe_subscription, 'currency') else subscription.currency)
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start) if hasattr(stripe_subscription, 'current_period_start') else subscription.current_period_start
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end) if hasattr(stripe_subscription, 'current_period_end') else subscription.current_period_end
            subscription.updated_at = datetime.utcnow()
            print(f"Payment success - Updated EXISTING subscription: Plan={plan_type}, ID={subscription.id}, User={current_user.username}")
        
        # Commit the new/updated subscription
        db.session.commit()
        print(f"Payment success - Committed subscription: ID={subscription.id}, Plan={subscription.plan_type}, Status={subscription.status}, User ID={subscription.user_id}")
        
        # Verify it was saved correctly
        verify_sub = db.session.query(Subscription).filter_by(id=subscription.id).first()
        print(f"Payment success - Verification query: ID={verify_sub.id}, Plan={verify_sub.plan_type}, Status={verify_sub.status}, User ID={verify_sub.user_id}")
        
        # CRITICAL: Force a complete refresh of all data
        # First, expire all cached relationships
        from sqlalchemy.orm import object_session
        session_obj = object_session(current_user)
        if session_obj:
            # Expire all relationships and attributes
            session_obj.expire_all()
        
        # Verify the subscription was created/updated correctly by querying fresh from DB
        # Use a new query to bypass any cache
        fresh_subscription = db.session.query(Subscription).filter_by(id=subscription.id).first()
        print(f"Payment success - Fresh subscription query: ID={fresh_subscription.id}, Plan={fresh_subscription.plan_type}, Status={fresh_subscription.status}")
        
        # Verify all subscriptions for this user
        all_subs = db.session.query(Subscription).filter_by(user_id=current_user.id).all()
        print(f"Payment success - All subscriptions for user after payment ({len(all_subs)}):")
        for sub in all_subs:
            print(f"  - ID: {sub.id}, Plan: {sub.plan_type}, Status: {sub.status}, Updated: {sub.updated_at}, User ID: {sub.user_id}")
        
        # Get active subscriptions directly
        all_active = db.session.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.status == 'active'
        ).order_by(Subscription.updated_at.desc()).all()
        print(f"Payment success - Active subscriptions query: {len(all_active)} found")
        for sub in all_active:
            print(f"  - ID: {sub.id}, Plan: {sub.plan_type}, Status: {sub.status}, Updated: {sub.updated_at}")
        
        # Get completely fresh user data from database (bypassing all caches)
        fresh_user = db.session.query(User).filter_by(id=current_user.id).first()
        
        # Force expire all relationships on fresh user
        if session_obj:
            session_obj.expire(fresh_user)
            session_obj.expire_all()
        
        # Now get the plan - this should query fresh from DB
        new_plan = fresh_user.get_plan()
        plan_name = PLANS.get(plan_type, {}).get('name', plan_type)
        print(f"Payment success - User: {fresh_user.username}, Plan from get_plan(): {new_plan} (expected: {plan_type})")
        
        if new_plan != plan_type:
            print(f"Payment success - ERROR: Plan mismatch! Expected {plan_type}, got {new_plan}")
            # Query directly to see what's happening
            print(f"Payment success - Direct active subscription query returned {len(all_active)} subscriptions")
            
            # If there's a mismatch, there might be multiple active subscriptions
            # Cancel all except the newest one
            if len(all_active) > 1:
                print(f"Payment success - WARNING: Multiple active subscriptions found! Canceling all except the newest")
                for sub in all_active[1:]:  # Skip the first (newest) one
                    sub.status = 'canceled'
                    sub.updated_at = datetime.utcnow()
                db.session.commit()
                # Re-query plan
                if session_obj:
                    session_obj.expire_all()
                fresh_user = db.session.query(User).filter_by(id=current_user.id).first()
                new_plan = fresh_user.get_plan()
                print(f"Payment success - After canceling duplicates, plan is now: {new_plan}")
            elif len(all_active) == 0:
                print(f"Payment success - ERROR: No active subscriptions found! This should not happen.")
                # Force create the subscription again if it doesn't exist
                if not subscription:
                    print(f"Payment success - Attempting to recreate subscription...")
                    subscription = Subscription(
                        user_id=current_user.id,
                        stripe_subscription_id=subscription_id,
                        stripe_customer_id=stripe_subscription.customer if hasattr(stripe_subscription, 'customer') else None,
                        status='active',
                        plan_type=plan_type,
                        amount=unit_amount / 100,
                        currency=(stripe_subscription.currency.upper() if hasattr(stripe_subscription, 'currency') else 'USD'),
                        current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start) if hasattr(stripe_subscription, 'current_period_start') else datetime.utcnow(),
                        current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end) if hasattr(stripe_subscription, 'current_period_end') else datetime.utcnow() + timedelta(days=30)
                    )
                    db.session.add(subscription)
                    db.session.commit()
                    print(f"Payment success - Recreated subscription: ID={subscription.id}, Plan={subscription.plan_type}")
        
        flash(f'Subscription activated successfully! Your plan has been updated to {plan_name}.', 'success')
        return redirect(url_for('payments.dashboard'))
    
    except Exception as e:
        flash(f'Error processing payment: {str(e)}', 'error')
        return redirect(url_for('payments.pricing'))

@payments_bp.route('/cancel')
@login_required
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled', 'info')
    return redirect(url_for('payments.pricing'))

@payments_bp.route('/dashboard')
@login_required
def dashboard():
    """User subscription dashboard"""
    # Refresh user object to get latest subscription data
    db.session.refresh(current_user)
    
    # Expire relationship cache to force fresh query
    from sqlalchemy.orm import object_session
    session = object_session(current_user)
    if session:
        session.expire(current_user, ['subscriptions'])
    
    subscription = current_user.get_active_subscription()
    plan_type = current_user.get_plan()
    plan = PLANS.get(plan_type, PLANS['free'])
    remaining_queries = current_user.get_remaining_queries()
    
    # Debug logging
    print(f"Dashboard - User: {current_user.username}, Plan: {plan_type}, Subscription: {subscription.plan_type if subscription else 'None'}")
    
    return render_template('dashboard.html', 
                         subscription=subscription,
                         user=current_user,
                         plan=plan,
                         plan_type=plan_type,
                         remaining_queries=remaining_queries,
                         all_plans=PLANS)

@payments_bp.route('/change-plan', methods=['POST'])
@login_required
def change_plan():
    """Change user's subscription plan"""
    try:
        data = request.json
        new_plan_type = data.get('plan_type')
        
        if not new_plan_type or new_plan_type not in PLANS:
            return jsonify({'error': 'Invalid plan type', 'success': False}), 400
        
        current_subscription = current_user.get_active_subscription()
        current_plan_type = current_user.get_plan()
        
        # If switching to the same plan
        if new_plan_type == current_plan_type:
            return jsonify({'error': 'You are already on this plan', 'success': False}), 400
        
        new_plan = PLANS[new_plan_type]
        
        # If switching to free plan
        if new_plan_type == 'free':
            # Cancel existing subscription if any
            if current_subscription and current_subscription.stripe_subscription_id:
                try:
                    stripe.Subscription.modify(
                        current_subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                except:
                    pass  # If Stripe fails, continue with local update
            
            # Create or update to free plan
            if current_subscription:
                current_subscription.plan_type = 'free'
                current_subscription.status = 'active'
                current_subscription.amount = 0
                current_subscription.updated_at = datetime.utcnow()
            else:
                new_subscription = Subscription(
                    user_id=current_user.id,
                    plan_type='free',
                    status='active',
                    amount=0,
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=365)
                )
                db.session.add(new_subscription)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Plan changed to Free successfully!',
                'requires_payment': False
            })
        
        # If switching to a paid plan (upgrade or downgrade)
        # Check if user is upgrading or downgrading
        current_price = PLANS.get(current_plan_type, PLANS['free']).get('price', 0)
        new_price = new_plan.get('price', 0)
        
        # If downgrading to a cheaper paid plan or upgrading
        # For paid plans, we need to go through Stripe checkout
        try:
            # Create or retrieve Stripe customer
            customer_id = None
            if current_subscription and current_subscription.stripe_customer_id:
                customer_id = current_subscription.stripe_customer_id
            else:
                # Create new Stripe customer
                customer = stripe.Customer.create(
                    email=current_user.email,
                    metadata={'user_id': str(current_user.id), 'username': current_user.username}
                )
                customer_id = customer.id
            
            # Determine interval
            interval = 'month' if new_plan['interval'] == 'month' else 'year'
            price_cents = PLAN_PRICES.get(new_plan_type, 0)
            
            # Create checkout session for plan change
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'AI Article Generator - {new_plan["name"]} Plan',
                            'description': get_plan_description(new_plan_type)
                        },
                        'recurring': {
                            'interval': interval
                        },
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.host_url + 'payment/dashboard',
                metadata={
                    'user_id': str(current_user.id),
                    'plan_type': new_plan_type,
                    'is_plan_change': 'true'
                }
            )
            
            return jsonify({
                'success': True,
                'requires_payment': True,
                'checkout_url': checkout_session.url,
                'message': 'Redirecting to payment...'
            })
        
        except Exception as e:
            return jsonify({'error': f'Error creating checkout session: {str(e)}', 'success': False}), 500
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user subscription"""
    try:
        subscription = current_user.get_active_subscription()
        
        if not subscription:
            return jsonify({'error': 'No active subscription found', 'success': False}), 404
        
        if subscription.stripe_subscription_id:
            # Cancel subscription in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
        
        subscription.status = 'canceled'
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subscription will be cancelled at the end of the current period'
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.updated':
        subscription_obj = event['data']['object']
        update_subscription_from_stripe(subscription_obj)
    elif event['type'] == 'customer.subscription.deleted':
        subscription_obj = event['data']['object']
        delete_subscription_from_stripe(subscription_obj)
    
    return jsonify({'status': 'success'}), 200

def update_subscription_from_stripe(stripe_subscription):
    """Update subscription in database from Stripe webhook"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription['id']
        ).first()
        
        if subscription:
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        print(f"Error updating subscription: {e}")

def delete_subscription_from_stripe(stripe_subscription):
    """Delete subscription from database from Stripe webhook"""
    try:
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=stripe_subscription['id']
        ).first()
        
        if subscription:
            subscription.status = 'canceled'
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
    except Exception as e:
        print(f"Error deleting subscription: {e}")

