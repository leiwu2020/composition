from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            if request.is_json:
                return jsonify({'error': 'All fields are required', 'success': False}), 400
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            if request.is_json:
                return jsonify({'error': 'Password must be at least 6 characters', 'success': False}), 400
            flash('Password must be at least 6 characters', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'error': 'Username already exists', 'success': False}), 400
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': 'Email already registered', 'success': False}), 400
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            
            # Auto-login after registration
            login_user(user, remember=True)
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'redirect': '/'
                })
            
            flash('Registration successful!', 'success')
            return redirect('/')
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': 'Registration failed: ' + str(e), 'success': False}), 500
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    # GET request - show registration form
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Username and password are required', 'success': False}), 400
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Find user by username or email
        user = User.query.filter_by(username=username).first() or User.query.filter_by(email=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                if request.is_json:
                    return jsonify({'error': 'Account is inactive', 'success': False}), 403
                flash('Account is inactive', 'error')
                return render_template('login.html')
            
            login_user(user, remember=bool(remember))
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/'
                })
            
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/')
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid username or password', 'success': False}), 401
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    # GET request - show login form
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

