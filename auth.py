"""
Authentication routes and forms for The Wish Machine
"""

from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from models import db, User, Waitlist
from email_service import email_service

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        errors = []

        # Validate email
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            errors.append(str(e))

        # Validate password
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')

        if password != password_confirm:
            errors.append('Passwords do not match')

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            errors.append('An account with this email already exists')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('signup.html')

        # Create new user
        try:
            new_user = User(
                email=email,
                subscription_tier='free'
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            # Log the user in
            login_user(new_user, remember=True)

            # Check if user has a pending subscription intent
            pending_tier = session.get('pending_subscription')
            current_app.logger.info(f'Signup complete for {email}. Pending subscription: {pending_tier}')

            if pending_tier:
                session.pop('pending_subscription')
                flash('Account created successfully! Redirecting to checkout...', 'success')
                current_app.logger.info(f'Redirecting new user to subscribe: {pending_tier}')
                return redirect(url_for('payments.subscribe', tier=pending_tier))

            flash('Account created successfully! Welcome to The Wish Machine.', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred creating your account. Please try again.', 'error')
            return render_template('signup.html')

    return render_template('signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=remember)
        flash('Logged in successfully!', 'success')

        # Redirect to next page if specified, otherwise go to index
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('index'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    from datetime import datetime, timezone

    # Call Flask-Login's logout_user() to remove user from session
    logout_user()

    # Store flash message
    flash('You have been logged out.', 'info')

    # Clear the entire session except flash messages
    # This is necessary because Flask-Login might leave data behind
    flashes = session.get('_flashes', [])
    session.clear()
    session['_flashes'] = flashes

    # Mark session as modified so Flask saves it
    session.modified = True

    # Create response
    response = redirect(url_for('index'))

    # Delete Flask-Login's "remember me" cookie (the persistent login cookie)
    # This cookie name is 'remember_token' by default in Flask-Login
    response.set_cookie('remember_token', '', expires=0, max_age=0, path='/',
                       domain=None, secure=True, httponly=True, samesite='Lax')

    return response


@auth_bp.route('/waitlist', methods=['GET', 'POST'])
def waitlist():
    """Waitlist signup page."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        name = request.form.get('name', '').strip()
        source = request.form.get('source', '').strip()

        # Validate email
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            flash(str(e), 'error')
            return render_template('waitlist.html')

        # Check if already on waitlist
        existing = Waitlist.query.filter_by(email=email).first()
        if existing:
            flash('You\'re already on the waitlist! We\'ll notify you soon.', 'info')
            return render_template('waitlist.html')

        # Check if user already has account
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('You already have an account! Please log in.', 'info')
            return redirect(url_for('auth.login'))

        # Add to waitlist
        try:
            waitlist_entry = Waitlist(
                email=email,
                name=name if name else None,
                source=source if source else None
            )
            db.session.add(waitlist_entry)
            db.session.commit()

            # Send confirmation email
            email_service.send_waitlist_confirmation(email, name)

            # Notify admin
            email_service.notify_admin_new_waitlist(email, name)

            flash('Success! You\'re on the waitlist. Check your email for confirmation.', 'success')
            return render_template('waitlist_success.html', email=email)

        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return render_template('waitlist.html')

    return render_template('waitlist.html')


@auth_bp.route('/api/waitlist', methods=['POST'])
def api_waitlist():
    """API endpoint for waitlist signup (for AJAX requests)."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()

        # Validate email
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({'error': str(e)}), 400

        # Check if already on waitlist
        existing = Waitlist.query.filter_by(email=email).first()
        if existing:
            return jsonify({'message': 'Already on waitlist'}), 200

        # Check if user already has account
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already has an account'}), 400

        # Add to waitlist
        waitlist_entry = Waitlist(
            email=email,
            name=name if name else None
        )
        db.session.add(waitlist_entry)
        db.session.commit()

        # Send confirmation email
        email_service.send_waitlist_confirmation(email, name)

        # Notify admin
        email_service.notify_admin_new_waitlist(email, name)

        return jsonify({'message': 'Successfully added to waitlist'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred'}), 500


@auth_bp.route('/account')
@login_required
def account():
    """User account page."""
    return render_template('account.html', user=current_user)


@auth_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile preferences (PRD Section 4)."""
    try:
        data = request.get_json()

        # Validate wish_themes (max 3)
        wish_themes = data.get('wish_themes', [])
        if not isinstance(wish_themes, list):
            return jsonify({'error': 'wish_themes must be an array'}), 400
        if len(wish_themes) > 3:
            return jsonify({'error': 'Maximum 3 themes allowed'}), 400

        # Validate open_to_connect (boolean)
        open_to_connect = data.get('open_to_connect', False)
        if not isinstance(open_to_connect, bool):
            return jsonify({'error': 'Invalid connect preference'}), 400

        # Update user
        current_user.wish_themes = wish_themes if wish_themes else None
        current_user.open_to_connect = open_to_connect
        db.session.commit()

        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error updating profile: {str(e)}')
        return jsonify({'error': 'An error occurred'}), 500
