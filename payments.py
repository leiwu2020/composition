from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, User, Subscription
from datetime import datetime, timedelta
import stripe
import os

payments_bp = Blueprint('payments', __name__)

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')

# Monthly subscription price (in cents) - $9.99/month
MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID', '')
MONTHLY_AMOUNT = 999  # $9.99 in cents

@payments_bp.route('/pricing')
def pricing():
    """Display pricing page"""
    return render_template('pricing.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
                         monthly_amount=MONTHLY_AMOUNT / 100)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        plan_type = request.json.get('plan_type', 'monthly')
        
        if plan_type != 'monthly':
            return jsonify({'error': 'Only monthly plans are currently available', 'success': False}), 400
        
        # Create or retrieve Stripe customer
        customer_id = None
        if current_user.subscriptions:
            # Check if user already has a Stripe customer ID
            existing_sub = Subscription.query.filter_by(
                user_id=current_user.id,
                stripe_customer_id__isnot=None
            ).first()
            if existing_sub:
                customer_id = existing_sub.stripe_customer_id
        
        if not customer_id:
            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': str(current_user.id), 'username': current_user.username}
            )
            customer_id = customer.id
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'AI Article Generator - Monthly Subscription',
                        'description': 'Unlimited article generation with AI'
                    },
                    'recurring': {
                        'interval': 'month'
                    },
                    'unit_amount': MONTHLY_AMOUNT,
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'payment/cancel',
            metadata={'user_id': str(current_user.id)}
        )
        
        return jsonify({
            'success': True,
            'sessionId': checkout_session.id,
            'url': checkout_session.url
        })
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

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
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Create or update subscription in database
        subscription = Subscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=current_user.id,
                stripe_subscription_id=subscription_id,
                stripe_customer_id=stripe_subscription.customer,
                status=stripe_subscription.status,
                plan_type='monthly',
                amount=stripe_subscription.items.data[0].price.unit_amount / 100,
                currency=stripe_subscription.currency.upper(),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
            )
            db.session.add(subscription)
        else:
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            subscription.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Subscription activated successfully!', 'success')
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
    subscription = current_user.get_active_subscription()
    return render_template('dashboard.html', 
                         subscription=subscription,
                         user=current_user)

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

