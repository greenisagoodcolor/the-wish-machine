"""
The Wish Machine - Web Interface
A beautiful UI for consciousness-influenced quantum collapse
Connected to PostgreSQL database.
"""

import os
import secrets
import hashlib
import time
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from dotenv import load_dotenv
import numpy as np

from quantum_state import UniverseState, WaveFunction, SpinUp, SpinDown
from choicemaker import ChoiceMaker, Observer
from models import db, bcrypt, User, Wish, EmailSubscriber
from auth import auth_bp
from payments import payments_bp
from admin_routes import admin_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///wishmachine.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = os.getenv('RAILWAY_ENVIRONMENT') == 'production'  # HTTPS only in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow session cookies across redirects
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request

# Make sessions permanent by default (persist across browser close)
@app.before_request
def make_session_permanent():
    """Make Flask sessions permanent by default."""
    session.permanent = True

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

# CSRF Protection
csrf = CSRFProtect(app)

# Security Headers with Flask-Talisman
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],  # unsafe-inline needed for inline scripts
    'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
    'font-src': ["'self'", 'https://fonts.gstatic.com'],
    'img-src': ["'self'", 'data:', 'https:'],
    'connect-src': ["'self'", 'https://api.stripe.com'],
}

# Initialize Talisman with security headers
# Only enforce HTTPS in production (Railway sets RAILWAY_ENVIRONMENT)
force_https = os.getenv('RAILWAY_ENVIRONMENT') == 'production'
Talisman(
    app,
    force_https=force_https,
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,  # 1 year
    content_security_policy=csp,
    # NOTE: nonce removed to allow inline scripts (required for MVP)
    # TODO: Add nonces to all inline scripts for production hardening
    x_content_type_options=True,
    frame_options='SAMEORIGIN',
)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(payments_bp)
app.register_blueprint(admin_bp)

# Exempt Stripe webhook from CSRF (uses signature verification instead)
csrf.exempt(app.view_functions['payments.stripe_webhook'])


class WishState:
    """Represents a wish outcome - manifested or not manifested."""

    def __init__(self, manifested=True):
        self.manifested = manifested
        self.name = "manifested" if manifested else "not_manifested"
        self.properties = {
            "manifested": manifested,
            "not_manifested": not manifested
        }

    def satisfies(self, preference):
        """Check if this state satisfies a preference."""
        return preference in self.properties and self.properties[preference]

    def __repr__(self):
        return f"WishState(manifested={self.manifested})"


def run_wish_simulation(wish_text, intensity):
    """
    Run the quantum collapse simulation for a wish.

    Args:
        wish_text: The user's wish
        intensity: Intention strength (1-100)

    Returns:
        dict: Simulation results including probability distribution
    """
    # Create universe state
    universe_state = UniverseState()

    # Create wish states: manifested vs not manifested
    manifested = WishState(manifested=True)
    not_manifested = WishState(manifested=False)
    states = [manifested, not_manifested]

    universe_state.wavefunction = WaveFunction(states=states)

    # === VARIANCE ALGORITHM ===
    # 1. Entropy from wish text (unique signature per wish)
    wish_hash = int(hashlib.md5(wish_text.encode()).hexdigest()[:8], 16)
    entropy_factor = 0.85 + (wish_hash % 300) / 1000  # 0.85 to 1.15

    # 2. Quantum noise (fundamental uncertainty)
    quantum_noise = np.random.uniform(0.8, 1.2)

    # 3. Temporal variance (time-based fluctuation)
    time_ms = int(time.time() * 1000)
    temporal_factor = 1.0 + (time_ms % 100) / 1000  # 1.0 to 1.1

    # 4. Non-linear preference scaling (prevents tanh saturation)
    # sqrt scaling: intensity 1-100 → preference 0.316 to 3.162
    base_preference = np.sqrt(intensity / 10) * entropy_factor

    # Apply variance to consciousness and preference
    consciousness_level = 10**15 * (intensity / 50) * quantum_noise * temporal_factor
    preference_strength = base_preference

    observer = Observer(
        consciousness_level=consciousness_level,
        location=(0, 0, 0),
        preferences={
            "manifested": preference_strength,
            "not_manifested": -preference_strength
        },
        time=0
    )
    universe_state.add_observer(observer)

    # Create choice maker
    choice_maker = ChoiceMaker(universe_state)

    # Run simulation and build histogram
    results = {"manifested": 0, "not_manifested": 0}
    num_trials = 1000

    for _ in range(num_trials):
        outcome = choice_maker.collapse(location=(0, 0, 0), time=1.0)
        results[outcome.name] += 1

    # Calculate statistics
    manifested_count = results["manifested"]
    not_manifested_count = results["not_manifested"]
    manifested_percent = (manifested_count / num_trials) * 100
    not_manifested_percent = (not_manifested_count / num_trials) * 100
    difference_from_baseline = manifested_percent - 50.0

    # === BUILD PROBABILITY DISTRIBUTION ===
    # Create histogram (100 buckets for 0-100%)
    trial_histogram = [0] * 100

    # Distribute trials around the manifested_percent with realistic variance
    # Using normal distribution to simulate quantum measurement uncertainty
    for _ in range(num_trials):
        # Add gaussian noise to create realistic probability cloud
        sample_value = manifested_percent + np.random.normal(0, 3.5)
        bucket_index = int(min(99, max(0, sample_value)))
        trial_histogram[bucket_index] += 1

    # Create baseline distribution (centered at 50% with narrow gaussian)
    baseline_histogram = []
    for i in range(100):
        # Gaussian centered at 50% with std dev of 5%
        baseline_value = int(1000 * np.exp(-((i - 50) ** 2) / (2 * 25)))
        baseline_histogram.append(baseline_value)

    return {
        "wish": wish_text,
        "intensity": intensity,
        "num_trials": num_trials,
        "manifested_count": manifested_count,
        "not_manifested_count": not_manifested_count,
        "manifested_percent": manifested_percent,
        "not_manifested_percent": not_manifested_percent,
        "difference_from_baseline": difference_from_baseline,
        "consciousness_level": consciousness_level,
        "preference_strength": preference_strength,
        "trial_histogram": trial_histogram,
        "baseline_histogram": baseline_histogram
    }


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', user=current_user)


@app.route('/app')
@login_required
def app_main():
    """Main wish-making app (requires login)."""
    return render_template('index.html', user=current_user)


@app.route('/pricing')
def pricing():
    """Pricing page."""
    return render_template('pricing.html')


@app.route('/make_wish', methods=['POST'])
@csrf.exempt  # AJAX endpoint - protected by rate limiting
@limiter.limit("30 per hour")
def make_wish():
    """Process a wish and return quantum collapse results. Allows one free anonymous wish."""
    try:
        data = request.get_json()
        wish_text = data.get('wish', '')
        intensity = int(data.get('intensity', 50))

        # Validate input
        if not wish_text:
            return jsonify({"error": "Wish text is required"}), 400

        if not (1 <= intensity <= 100):
            return jsonify({"error": "Intensity must be between 1 and 100"}), 400

        if len(wish_text) > 500:
            return jsonify({"error": "Wish text must be 500 characters or less"}), 400

        # Check if user is authenticated or anonymous
        is_authenticated = current_user.is_authenticated

        if is_authenticated:
            # Authenticated user - check their wish limit
            if not current_user.can_make_wish():
                limit = current_user.get_wish_limit()
                return jsonify({
                    "error": f"You've reached your monthly limit of {limit} wishes. Please upgrade your plan.",
                    "limit_reached": True,
                    "current_tier": current_user.subscription_tier
                }), 429
        else:
            # Anonymous user - check session for free wish (max 1)
            anonymous_wishes = session.get('anonymous_wish_count', 0)
            if anonymous_wishes >= 1:
                return jsonify({
                    "error": "You've used your free wish. Sign up for 10 free wishes per month!",
                    "limit_reached": True,
                    "anonymous": True,
                    "show_upsell": True
                }), 429

        # Run simulation
        results = run_wish_simulation(wish_text, intensity)

        # Save wish to database for both authenticated and anonymous users
        wish_record = Wish(
            user_id=current_user.id if is_authenticated else None,  # NULL for anonymous
            wish_text=wish_text,
            intensity=intensity,
            manifested_percent=results['manifested_percent'],
            not_manifested_percent=results['not_manifested_percent'],
            difference_from_baseline=results['difference_from_baseline'],
            manifested_count=results['manifested_count'],
            not_manifested_count=results['not_manifested_count'],
            num_trials=results['num_trials'],
            consciousness_level=results['consciousness_level'],
            preference_strength=results['preference_strength'],
            ip_address=request.remote_addr
        )
        db.session.add(wish_record)
        db.session.commit()

        if is_authenticated:
            # Increment counter for authenticated users
            current_user.increment_wish_count()

            # Add usage info to response
            results['wishes_remaining'] = current_user.get_wish_limit() - current_user.wishes_this_month
            results['wishes_used'] = current_user.wishes_this_month
            results['wish_limit'] = current_user.get_wish_limit()
            results['subscription_tier'] = current_user.subscription_tier
            results['anonymous'] = False
        else:
            # Anonymous user - increment session counter
            session['anonymous_wish_count'] = anonymous_wishes + 1
            results['anonymous'] = True
            results['show_modal'] = True  # Trigger modal on frontend

        return jsonify(results)

    except Exception as e:
        app.logger.error(f'Error making wish: {str(e)}')
        db.session.rollback()
        return jsonify({"error": "An error occurred processing your wish"}), 500


@app.route('/my-wishes')
@login_required
def my_wishes():
    """View user's wish history."""
    page = request.args.get('page', 1, type=int)
    wishes = Wish.query.filter_by(user_id=current_user.id)\
        .order_by(Wish.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)

    return render_template('wishes_history.html', wishes=wishes)


@app.route('/api/recent-wishes')
def recent_wishes():
    """Get the last 5 wishes (anonymized) for the community feed."""
    try:
        recent = Wish.query.order_by(Wish.created_at.desc()).limit(5).all()

        wishes_data = []
        for wish in recent:
            # Truncate wish text to 60 characters for privacy and brevity
            wish_preview = wish.wish_text[:60] + '...' if len(wish.wish_text) > 60 else wish.wish_text

            # Calculate time ago
            now = datetime.now(timezone.utc)
            # Ensure wish.created_at is timezone-aware
            created_at = wish.created_at if wish.created_at.tzinfo else wish.created_at.replace(tzinfo=timezone.utc)
            delta = now - created_at
            if delta.seconds < 60:
                time_ago = "just now"
            elif delta.seconds < 3600:
                mins = delta.seconds // 60
                time_ago = f"{mins}m ago"
            elif delta.seconds < 86400:
                hours = delta.seconds // 3600
                time_ago = f"{hours}h ago"
            else:
                days = delta.days
                time_ago = f"{days}d ago"

            wishes_data.append({
                'wish': wish_preview,
                'manifested_percent': round(wish.manifested_percent, 1),
                'time_ago': time_ago,
                'intensity': wish.intensity
            })

        return jsonify(wishes_data)

    except Exception as e:
        app.logger.error(f'Error fetching recent wishes: {str(e)}')
        return jsonify([]), 200  # Return empty array on error


@app.route('/api/subscribe-email', methods=['POST'])
@csrf.exempt  # AJAX endpoint - protected by rate limiting
@limiter.limit("10 per hour")
def subscribe_email():
    """Subscribe an email for wish mates, tips, and consciousness education."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        # Validate email
        if not email:
            return jsonify({"error": "Email is required"}), 400

        # Basic email format validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({"error": "Please enter a valid email address"}), 400

        # Check if already subscribed
        existing = EmailSubscriber.query.filter_by(email=email).first()
        if existing:
            if existing.status == 'active':
                return jsonify({
                    "message": "You're already subscribed! Check your inbox for updates.",
                    "already_subscribed": True
                }), 200
            elif existing.status == 'unsubscribed':
                # Resubscribe
                existing.status = 'active'
                existing.unsubscribed_at = None
                existing.confirmation_token = secrets.token_urlsafe(32)
                db.session.commit()
                return jsonify({
                    "message": "Welcome back! You've been resubscribed.",
                    "success": True
                }), 200

        # Create new subscriber
        subscriber = EmailSubscriber(
            email=email,
            wants_wish_mates=data.get('wants_wish_mates', True),
            wants_tips=data.get('wants_tips', True),
            wants_education=data.get('wants_education', True),
            confirmation_token=secrets.token_urlsafe(32),
            source=data.get('source', 'post_wish_modal'),
            ip_address=request.remote_addr
        )

        db.session.add(subscriber)
        db.session.commit()

        return jsonify({
            "message": "Thank you! You'll hear from us soon with wish mate matches and consciousness insights.",
            "success": True
        }), 201

    except Exception as e:
        app.logger.error(f'Error subscribing email: {str(e)}')
        db.session.rollback()
        return jsonify({"error": "An error occurred. Please try again."}), 500


@app.route('/debug/stripe-status')
def stripe_status():
    """Debug endpoint to verify Stripe configuration across workers."""
    import stripe
    worker_pid = os.getpid()

    # Check if Stripe API key is set
    api_key_set = bool(stripe.api_key)

    # Safely show partial API key
    if stripe.api_key:
        api_key_preview = f"{stripe.api_key[:10]}...{stripe.api_key[-4:]}"
    else:
        api_key_preview = "NOT SET"

    # Get price IDs from environment
    price_single = os.getenv('STRIPE_PRICE_ID_SINGLE', 'NOT SET')
    price_premium = os.getenv('STRIPE_PRICE_ID_PREMIUM', 'NOT SET')
    price_unlimited = os.getenv('STRIPE_PRICE_ID_UNLIMITED', 'NOT SET')

    return jsonify({
        "worker_pid": worker_pid,
        "stripe_api_key_set": api_key_set,
        "stripe_api_key_preview": api_key_preview,
        "stripe_price_id_single": price_single,
        "stripe_price_id_premium": price_premium,
        "stripe_price_id_unlimited": price_unlimited,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# Database initialization
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")


@app.cli.command()
def create_admin():
    """Create an admin user."""
    email = input("Admin email: ")
    password = input("Admin password: ")

    admin = User(email=email, subscription_tier='unlimited')
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {email}")


@app.cli.command()
def migrate_phase_1_4():
    """Run Phase 1-4 database migrations."""
    from sqlalchemy import inspect, text

    print("="*60)
    print("Phase 1-4 Database Migrations")
    print("="*60)

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f'\n✓ Found {len(tables)} existing tables')

    # 1. Create email_subscribers table if needed
    if 'email_subscribers' not in tables:
        print('\n→ Creating email_subscribers table...')
        EmailSubscriber.__table__.create(db.engine)
        print('✓ email_subscribers table created')
    else:
        print('\n✓ email_subscribers table exists')

    # 2. Make wishes.user_id nullable if needed
    if 'wishes' in tables:
        columns = inspector.get_columns('wishes')
        user_id_col = next((c for c in columns if c['name'] == 'user_id'), None)

        if user_id_col and not user_id_col.get('nullable', False):
            print('\n→ Making wishes.user_id nullable...')
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE wishes ALTER COLUMN user_id DROP NOT NULL'))
                conn.commit()
            print('✓ wishes.user_id is now nullable')
        else:
            print('\n✓ wishes.user_id is already nullable')

    print('\n✅ All migrations completed!')
    print("="*60)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("✨ THE WISH MACHINE ✨")
    print("="*60)
    print("\nStarting web server...")
    print("Open your browser to: http://localhost:8080")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    app.run(debug=True, host='0.0.0.0', port=8080)
