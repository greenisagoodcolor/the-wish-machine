"""
Stripe payment integration for The Wish Machine
"""

import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import stripe
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user, login_user
from models import db, User, Payment
from flask_wtf.csrf import csrf
from email_service import email_service

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

payments_bp = Blueprint('payments', __name__)


class StripeService:
    """Service for handling Stripe operations."""

    def __init__(self) -> None:
        """Initialize Stripe service."""
        self.public_key = os.getenv('STRIPE_PUBLIC_KEY')
        self.secret_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.price_id_premium = os.getenv('STRIPE_PRICE_ID_PREMIUM')
        self.price_id_unlimited = os.getenv('STRIPE_PRICE_ID_UNLIMITED')
        self.price_id_single = os.getenv('STRIPE_PRICE_ID_SINGLE')

    def create_checkout_session(self, user: User, tier: str, success_url: str, cancel_url: str) -> Optional[str]:
        """
        Create a Stripe checkout session for subscription.

        Args:
            user: User object
            tier: Subscription tier (premium/unlimited)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL or None
        """
        try:
            # Get the appropriate price ID
            price_id = self.price_id_premium if tier == 'premium' else self.price_id_unlimited

            if not price_id:
                current_app.logger.error(f'No price ID configured for tier: {tier}')
                return None

            # Create or get Stripe customer
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': user.id}
                )
                user.stripe_customer_id = customer.id
                db.session.commit()

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'tier': tier
                }
            )

            return session.url

        except Exception as e:
            current_app.logger.error(f'Error creating checkout session: {str(e)}')
            return None

    def create_guest_wish_checkout(self, success_url: str, cancel_url: str, session_id: str) -> Optional[str]:
        """
        Create a Stripe checkout session for anonymous guest wish purchase.

        Args:
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            session_id: Flask session ID to track the guest

        Returns:
            Checkout session URL or None
        """
        try:
            if not self.price_id_single:
                current_app.logger.error('No price ID configured for single wish')
                return None

            # Create checkout session for guest (no pre-existing customer)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': self.price_id_single,
                    'quantity': 1,
                }],
                mode='payment',  # One-time payment
                success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url,
                billing_address_collection='required',  # Collect email
                client_reference_id=session_id,  # Track session
                metadata={
                    'guest_purchase': 'true',
                    'session_id': session_id
                }
            )

            return checkout_session.url

        except Exception as e:
            current_app.logger.error(f'Error creating guest wish checkout: {str(e)}')
            return None

    def create_single_wish_checkout(self, user: User, success_url: str, cancel_url: str) -> Optional[str]:
        """
        Create a Stripe checkout session for one-time wish purchase.

        Args:
            user: User object
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL or None
        """
        try:
            if not self.price_id_single:
                current_app.logger.error('No price ID configured for single wish')
                return None

            # Create or get Stripe customer
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': user.id}
                )
                user.stripe_customer_id = customer.id
                db.session.commit()

            # Create checkout session for one-time payment
            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.price_id_single,
                    'quantity': 1,
                }],
                mode='payment',  # One-time payment, not subscription
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'purchase_type': 'single_wish'
                }
            )

            return session.url

        except Exception as e:
            current_app.logger.error(f'Error creating single wish checkout: {str(e)}')
            return None

    def create_customer_portal_session(self, user: User, return_url: str) -> Optional[str]:
        """
        Create a Stripe customer portal session for managing subscriptions.

        Args:
            user: User object
            return_url: URL to return to after portal session

        Returns:
            Portal session URL or None
        """
        try:
            if not user.stripe_customer_id:
                current_app.logger.error(f'User {user.id} has no Stripe customer ID')
                return None

            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url
            )

            return session.url

        except Exception as e:
            current_app.logger.error(f'Error creating portal session: {str(e)}')
            return None

    def handle_checkout_completed(self, session: Dict[str, Any]) -> None:
        """
        Handle successful checkout completion.

        Args:
            session: Stripe checkout session object
        """
        try:
            # Check if this is a guest purchase
            is_guest_purchase = session['metadata'].get('guest_purchase') == 'true'

            if is_guest_purchase:
                # Guest purchase - create new user account
                customer_details = session.get('customer_details', {})
                email = customer_details.get('email')

                if not email:
                    current_app.logger.error('No email found in guest checkout session')
                    return

                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()

                if existing_user:
                    # User exists - just add bonus wish
                    existing_user.bonus_wishes += 1
                    existing_user.updated_at = datetime.now(timezone.utc)
                    db.session.commit()
                    current_app.logger.info(f'Added bonus wish to existing user {existing_user.id}')
                    return

                # Create new user account
                import secrets
                new_user = User(
                    email=email,
                    subscription_tier='free',
                    bonus_wishes=1  # Grant the purchased wish
                )
                # Set a random secure password (user will need to reset if they want to login with password)
                new_user.set_password(secrets.token_urlsafe(32))

                # Add Stripe customer info if available
                if session.get('customer'):
                    new_user.stripe_customer_id = session['customer']

                db.session.add(new_user)
                db.session.commit()

                current_app.logger.info(f'Created new user account for guest purchase: {email} (ID: {new_user.id})')

                # Note: We can't directly set Flask session from webhook
                # The frontend will need to handle login after purchase
                return

            # Regular checkout for existing users
            user_id = int(session['metadata']['user_id'])
            purchase_type = session['metadata'].get('purchase_type')

            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f'User {user_id} not found for checkout completion')
                return

            # Handle one-time wish purchase
            if purchase_type == 'single_wish':
                user.bonus_wishes += 1
                user.updated_at = datetime.now(timezone.utc)
                db.session.commit()
                current_app.logger.info(f'User {user_id} purchased one special wish')
                return

            # Handle subscription purchase
            tier = session['metadata']['tier']
            subscription_id = session['subscription']

            # Update user subscription
            user.subscription_tier = tier
            user.stripe_subscription_id = subscription_id
            user.subscription_status = 'active'
            user.updated_at = datetime.now(timezone.utc)

            # Reset wish count for new tier
            user.wishes_this_month = 0
            user.last_wish_reset = datetime.now(timezone.utc)

            db.session.commit()

            # Send confirmation email
            amount = 9.99 if tier == 'premium' else 29.99
            email_service.send_subscription_confirmation(user.email, tier, amount)

            current_app.logger.info(f'User {user_id} upgraded to {tier}')

        except Exception as e:
            current_app.logger.error(f'Error handling checkout completion: {str(e)}')
            db.session.rollback()

    def handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        """
        Handle subscription updates (renewals, cancellations, etc.).

        Args:
            subscription: Stripe subscription object
        """
        try:
            subscription_id = subscription['id']
            status = subscription['status']

            user = User.query.filter_by(stripe_subscription_id=subscription_id).first()
            if not user:
                current_app.logger.error(f'User not found for subscription {subscription_id}')
                return

            user.subscription_status = status
            user.updated_at = datetime.now(timezone.utc)

            # If subscription is canceled or past_due, downgrade to free
            if status in ['canceled', 'unpaid']:
                user.subscription_tier = 'free'
                user.wishes_this_month = 0
                current_app.logger.info(f'User {user.id} downgraded to free tier')

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f'Error handling subscription update: {str(e)}')
            db.session.rollback()

    def handle_invoice_payment_succeeded(self, invoice: Dict[str, Any]) -> None:
        """
        Handle successful invoice payment.

        Args:
            invoice: Stripe invoice object
        """
        try:
            customer_id = invoice['customer']
            subscription_id = invoice['subscription']
            amount = invoice['amount_paid']

            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if not user:
                current_app.logger.error(f'User not found for customer {customer_id}')
                return

            # Record payment
            payment = Payment(
                user_id=user.id,
                stripe_invoice_id=invoice['id'],
                amount=amount,
                currency=invoice['currency'],
                status='succeeded',
                subscription_tier=user.subscription_tier,
                billing_period_start=datetime.fromtimestamp(invoice['period_start']),
                billing_period_end=datetime.fromtimestamp(invoice['period_end'])
            )

            db.session.add(payment)
            db.session.commit()

            current_app.logger.info(f'Payment recorded for user {user.id}: ${amount/100:.2f}')

        except Exception as e:
            current_app.logger.error(f'Error handling invoice payment: {str(e)}')
            db.session.rollback()


# Global Stripe service instance
stripe_service = StripeService()


@payments_bp.route('/subscribe/<tier>')
def subscribe(tier: str):
    """Create a checkout session for subscription."""
    if tier not in ['premium', 'unlimited']:
        flash('Invalid subscription tier', 'error')
        return redirect(url_for('index'))

    # Handle anonymous users - store intent and redirect to signup
    if not current_user.is_authenticated:
        session['pending_subscription'] = tier
        flash(f'Please sign up to subscribe to the {tier} plan', 'info')
        return redirect(url_for('auth.signup'))

    # Check if already subscribed to this tier
    if current_user.subscription_tier == tier and current_user.subscription_status == 'active':
        flash(f'You are already subscribed to the {tier} plan', 'info')
        return redirect(url_for('auth.account'))

    # Create checkout session
    success_url = url_for('payments.subscription_success', _external=True)
    cancel_url = url_for('index', _external=True)

    checkout_url = stripe_service.create_checkout_session(
        user=current_user,
        tier=tier,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not checkout_url:
        flash('Error creating checkout session. Stripe Price IDs may not be configured.', 'error')
        return redirect(url_for('index'))

    return redirect(checkout_url)


@payments_bp.route('/buy-single-wish')
@login_required
def buy_single_wish():
    """Create a checkout session for one-time wish purchase (logged-in users)."""
    # Create checkout session
    success_url = url_for('payments.purchase_success', _external=True)
    cancel_url = url_for('index', _external=True)

    checkout_url = stripe_service.create_single_wish_checkout(
        user=current_user,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not checkout_url:
        flash('Error creating checkout session. Please try again.', 'error')
        return redirect(url_for('index'))

    return redirect(checkout_url)


@payments_bp.route('/buy-single-wish-guest')
def buy_single_wish_guest():
    """Create a checkout session for anonymous guest wish purchase."""
    # Store a reference in session to track this purchase
    import secrets
    session['guest_purchase_ref'] = secrets.token_urlsafe(16)

    # Create checkout session for guest
    success_url = url_for('payments.guest_purchase_success', _external=True)
    cancel_url = url_for('index', _external=True)

    checkout_url = stripe_service.create_guest_wish_checkout(
        success_url=success_url,
        cancel_url=cancel_url,
        session_id=session['guest_purchase_ref']
    )

    if not checkout_url:
        flash('Error creating checkout session. Please try again.', 'error')
        return redirect(url_for('index'))

    return redirect(checkout_url)


@payments_bp.route('/subscription/success')
@login_required
def subscription_success():
    """Subscription success page."""
    flash('Subscription activated! Welcome to your new plan.', 'success')
    return redirect(url_for('auth.account'))


@payments_bp.route('/purchase/success')
@login_required
def purchase_success():
    """One-time purchase success page (logged-in users)."""
    flash('Purchase successful! Your special wish has been added to your account.', 'success')
    return redirect(url_for('app_main'))


@payments_bp.route('/guest-purchase/success')
def guest_purchase_success():
    """Guest purchase success page with auto-login."""
    # Get the checkout session ID from Stripe redirect
    checkout_session_id = request.args.get('session_id')

    if checkout_session_id:
        try:
            # Retrieve the Stripe checkout session to get customer email
            checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)
            customer_email = checkout_session.customer_details.email if checkout_session.customer_details else None

            if customer_email:
                # Find the user account (created by webhook or already exists)
                user = User.query.filter_by(email=customer_email).first()

                if user:
                    # Auto-login the user
                    login_user(user, remember=True)
                    session.pop('guest_purchase_ref', None)
                    session.pop('anonymous_wish_count', None)  # Reset anonymous counter

                    flash('Welcome! Your wish has been added to your account.', 'success')
                    return redirect(url_for('index'))
                else:
                    # User not created yet - webhook might be delayed
                    current_app.logger.warning(f'Guest purchase: User with email {customer_email} not found yet')
        except Exception as e:
            current_app.logger.error(f'Error in guest purchase success: {str(e)}')

    # Fallback if session ID missing or user not found
    flash('Payment successful! Check your email for account details.', 'info')
    return redirect(url_for('index'))


@payments_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    """Redirect to Stripe customer portal."""
    if not current_user.stripe_customer_id:
        flash('No subscription to manage', 'info')
        return redirect(url_for('auth.account'))

    return_url = url_for('auth.account', _external=True)
    portal_url = stripe_service.create_customer_portal_session(current_user, return_url)

    if not portal_url:
        flash('Error accessing subscription management. Please try again.', 'error')
        return redirect(url_for('auth.account'))

    return redirect(portal_url)


@payments_bp.route('/webhook', methods=['POST'])
@csrf.exempt  # Webhook from Stripe - uses signature verification instead
def stripe_webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_service.webhook_secret
        )
    except ValueError as e:
        current_app.logger.error(f'Invalid webhook payload: {str(e)}')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f'Invalid webhook signature: {str(e)}')
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle different event types
    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        stripe_service.handle_checkout_completed(data)
    elif event_type == 'customer.subscription.updated':
        stripe_service.handle_subscription_updated(data)
    elif event_type == 'customer.subscription.deleted':
        stripe_service.handle_subscription_updated(data)
    elif event_type == 'invoice.payment_succeeded':
        stripe_service.handle_invoice_payment_succeeded(data)
    else:
        current_app.logger.info(f'Unhandled webhook event type: {event_type}')

    return jsonify({'status': 'success'}), 200
