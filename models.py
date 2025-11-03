"""
Database models for The Wish Machine
"""

from datetime import datetime, timezone
from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """User account model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Subscription info
    subscription_tier = db.Column(db.String(50), default='free', nullable=False)  # free, premium, unlimited
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=True)
    subscription_status = db.Column(db.String(50), default='active', nullable=False)  # active, canceled, past_due

    # Usage tracking
    wishes_this_month = db.Column(db.Integer, default=0, nullable=False)
    total_wishes = db.Column(db.Integer, default=0, nullable=False)
    last_wish_reset = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    bonus_wishes = db.Column(db.Integer, default=0, nullable=False)  # Purchased one-time wishes

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    wishes = db.relationship('Wish', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_wish_limit(self) -> int:
        """Get the maximum number of wishes allowed per month for this user's tier."""
        limits = {
            'free': 3,        # Updated from 1 per PRD
            'premium': 10,
            'unlimited': 999999
        }
        return limits.get(self.subscription_tier, 3)

    def can_make_wish(self) -> bool:
        """Check if user has wishes remaining this month."""
        # Check bonus wishes first (with graceful fallback for older database schemas)
        try:
            if hasattr(self, 'bonus_wishes') and self.bonus_wishes > 0:
                return True
        except:
            pass

        # Reset counter if it's a new month
        now = datetime.now(timezone.utc)
        if self.last_wish_reset.month != now.month or self.last_wish_reset.year != now.year:
            self.wishes_this_month = 0
            self.last_wish_reset = now
            db.session.commit()

        return self.wishes_this_month < self.get_wish_limit()

    def increment_wish_count(self) -> None:
        """Increment the wish counter."""
        # Use bonus wishes first (with graceful fallback for older database schemas)
        try:
            if hasattr(self, 'bonus_wishes') and self.bonus_wishes > 0:
                self.bonus_wishes -= 1
            else:
                self.wishes_this_month += 1
        except:
            self.wishes_this_month += 1

        self.total_wishes += 1
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class Waitlist(db.Model):
    """Waitlist entries for early access."""
    __tablename__ = 'waitlist'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=True)

    # Status tracking
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, invited, converted
    invited_at = db.Column(db.DateTime, nullable=True)
    converted_at = db.Column(db.DateTime, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    source = db.Column(db.String(100), nullable=True)  # How they found us
    referral_code = db.Column(db.String(50), nullable=True)

    def __repr__(self) -> str:
        return f'<Waitlist {self.email}>'


class Wish(db.Model):
    """Individual wish records."""
    __tablename__ = 'wishes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Nullable to support anonymous wishes

    # Wish details
    wish_text = db.Column(db.Text, nullable=False)
    intensity = db.Column(db.Integer, nullable=False)

    # Results
    manifested_percent = db.Column(db.Float, nullable=False)
    not_manifested_percent = db.Column(db.Float, nullable=False)
    difference_from_baseline = db.Column(db.Float, nullable=False)
    manifested_count = db.Column(db.Integer, nullable=False)
    not_manifested_count = db.Column(db.Integer, nullable=False)
    num_trials = db.Column(db.Integer, default=1000, nullable=False)

    # Technical details
    consciousness_level = db.Column(db.Float, nullable=False)
    preference_strength = db.Column(db.Float, nullable=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible

    def __repr__(self) -> str:
        return f'<Wish {self.id} by User {self.user_id}>'


class Payment(db.Model):
    """Payment transaction records."""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Stripe details
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, nullable=True)
    stripe_invoice_id = db.Column(db.String(255), unique=True, nullable=True)

    # Payment info
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), default='usd', nullable=False)
    status = db.Column(db.String(50), nullable=False)  # succeeded, pending, failed

    # Subscription info
    subscription_tier = db.Column(db.String(50), nullable=False)
    billing_period_start = db.Column(db.DateTime, nullable=True)
    billing_period_end = db.Column(db.DateTime, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    user = db.relationship('User', backref='payments')

    def __repr__(self) -> str:
        return f'<Payment {self.id} - ${self.amount/100:.2f}>'


class EmailSubscriber(db.Model):
    """Email subscribers for wish mates, tips, and consciousness education."""
    __tablename__ = 'email_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # Preferences
    wants_wish_mates = db.Column(db.Boolean, default=True, nullable=False)  # Match with similar wishers
    wants_tips = db.Column(db.Boolean, default=True, nullable=False)  # Tips on intentions, consciousness
    wants_education = db.Column(db.Boolean, default=True, nullable=False)  # Wave-particle duality, quantum mechanics

    # Status tracking
    status = db.Column(db.String(50), default='active', nullable=False)  # active, unsubscribed, bounced
    confirmed = db.Column(db.Boolean, default=False, nullable=False)  # Email confirmed via double opt-in
    confirmation_token = db.Column(db.String(100), nullable=True, unique=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    source = db.Column(db.String(100), nullable=True)  # post_wish_modal, pricing_page, etc.
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible

    def __repr__(self) -> str:
        return f'<EmailSubscriber {self.email}>'
