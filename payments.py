"""
Stripe payment integration for The Wish Machine
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
import stripe
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, User, Payment
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
            user_id = int(session['metadata']['user_id'])
            purchase_type = session['metadata'].get('purchase_type')

            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f'User {user_id} not found for checkout completion')
                return

            # Handle one-time wish purchase
            if purchase_type == 'single_wish':
                user.bonus_wishes += 1
                user.updated_at = datetime.utcnow()
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
            user.updated_at = datetime.utcnow()

            # Reset wish count for new tier
            user.wishes_this_month = 0
            user.last_wish_reset = datetime.utcnow()

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
            user.updated_at = datetime.utcnow()

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
@login_required
def subscribe(tier: str):
    """Create a checkout session for subscription."""
    if tier not in ['premium', 'unlimited']:
        flash('Invalid subscription tier', 'error')
        return redirect(url_for('pricing'))

    # Check if already subscribed to this tier
    if current_user.subscription_tier == tier and current_user.subscription_status == 'active':
        flash(f'You are already subscribed to the {tier} plan', 'info')
        return redirect(url_for('auth.account'))

    # Create checkout session
    success_url = url_for('payments.subscription_success', _external=True)
    cancel_url = url_for('pricing', _external=True)

    checkout_url = stripe_service.create_checkout_session(
        user=current_user,
        tier=tier,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not checkout_url:
        flash('Error creating checkout session. Please try again.', 'error')
        return redirect(url_for('pricing'))

    return redirect(checkout_url)


@payments_bp.route('/buy-single-wish')
@login_required
def buy_single_wish():
    """Create a checkout session for one-time wish purchase."""
    # Create checkout session
    success_url = url_for('payments.purchase_success', _external=True)
    cancel_url = url_for('pricing', _external=True)

    checkout_url = stripe_service.create_single_wish_checkout(
        user=current_user,
        success_url=success_url,
        cancel_url=cancel_url
    )

    if not checkout_url:
        flash('Error creating checkout session. Please try again.', 'error')
        return redirect(url_for('pricing'))

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
    """One-time purchase success page."""
    flash('Purchase successful! Your special wish has been added to your account.', 'success')
    return redirect(url_for('app_main'))


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
