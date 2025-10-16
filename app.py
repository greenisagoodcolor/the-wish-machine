"""
The Wish Machine - Web Interface
A beautiful UI for consciousness-influenced quantum collapse
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import numpy as np

from quantum_state import UniverseState, WaveFunction, SpinUp, SpinDown
from choicemaker import ChoiceMaker, Observer
from models import db, bcrypt, User, Wish
from auth import auth_bp
from payments import payments_bp

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

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

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
        dict: Simulation results
    """
    # Create universe state
    universe_state = UniverseState()

    # Create wish states: manifested vs not manifested
    manifested = WishState(manifested=True)
    not_manifested = WishState(manifested=False)
    states = [manifested, not_manifested]

    universe_state.wavefunction = WaveFunction(states=states)

    # Create observer with preference for manifestation
    # Intensity scales the consciousness level and preference strength
    consciousness_level = 10**15 * (intensity / 50)  # Scale around human baseline
    preference_strength = intensity / 50  # 1.0 at 50%, 2.0 at 100%

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

    # Run simulation
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
        "preference_strength": preference_strength
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
@login_required
@limiter.limit("30 per hour")
def make_wish():
    """Process a wish and return quantum collapse results."""
    try:
        # Check if user has wishes remaining
        if not current_user.can_make_wish():
            limit = current_user.get_wish_limit()
            return jsonify({
                "error": f"You've reached your monthly limit of {limit} wishes. Please upgrade your plan.",
                "limit_reached": True,
                "current_tier": current_user.subscription_tier
            }), 429

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

        # Run simulation
        results = run_wish_simulation(wish_text, intensity)

        # Increment user's wish count
        current_user.increment_wish_count()

        # Save wish to database
        wish_record = Wish(
            user_id=current_user.id,
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

        # Add usage info to response
        results['wishes_remaining'] = current_user.get_wish_limit() - current_user.wishes_this_month
        results['wishes_used'] = current_user.wishes_this_month
        results['wish_limit'] = current_user.get_wish_limit()
        results['subscription_tier'] = current_user.subscription_tier

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
