"""
Email service for The Wish Machine
Handles waitlist notifications and transactional emails
"""

import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from flask import current_app


class EmailService:
    """Service for sending emails via SendGrid."""

    def __init__(self) -> None:
        """Initialize the email service."""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@wishmachine.app')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'admin@wishmachine.app')
        self.client: Optional[SendGridAPIClient] = None

        if self.api_key:
            self.client = SendGridAPIClient(self.api_key)

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            current_app.logger.warning('SendGrid client not configured. Email not sent.')
            return False

        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.client.send(message)
            current_app.logger.info(f'Email sent to {to_email}: {response.status_code}')
            return response.status_code in [200, 201, 202]

        except Exception as e:
            current_app.logger.error(f'Error sending email to {to_email}: {str(e)}')
            return False

    def send_waitlist_confirmation(self, email: str, name: Optional[str] = None) -> bool:
        """
        Send waitlist confirmation email.

        Args:
            email: Email address
            name: Optional name

        Returns:
            True if sent successfully
        """
        greeting = f'Hi {name}' if name else 'Hi there'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">✨</div>
                <h1>Welcome to The Wish Machine</h1>
            </div>

            <div class="content">
                <p>{greeting},</p>

                <p>Thank you for joining The Wish Machine waitlist! You're among the first to experience consciousness-influenced quantum reality.</p>

                <p><strong>What happens next?</strong></p>
                <ul>
                    <li>You'll get early access when we launch</li>
                    <li>Exclusive founding member pricing</li>
                    <li>Behind-the-scenes updates on development</li>
                    <li>First dibs on premium features</li>
                </ul>

                <p>We're working hard to bring The Wish Machine to life. In the meantime, prepare your intentions and get ready to influence quantum reality!</p>

                <p style="margin-top: 30px;">
                    <strong>The Wish Machine Team</strong><br>
                    Where intention meets quantum mechanics
                </p>
            </div>

            <div class="footer">
                <p>You're receiving this because you signed up for The Wish Machine waitlist.</p>
                <p>&copy; 2024 The Wish Machine. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            to_email=email,
            subject='Welcome to The Wish Machine Waitlist!',
            html_content=html_content
        )

    def send_waitlist_invite(self, email: str, invite_link: str) -> bool:
        """
        Send early access invitation.

        Args:
            email: Email address
            invite_link: Unique signup link

        Returns:
            True if sent successfully
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">✨</div>
                <h1>Your Early Access is Ready!</h1>
            </div>

            <div class="content">
                <p>Great news! The Wish Machine is live, and you're invited to be among the first users.</p>

                <p><strong>Here's what you get as an early member:</strong></p>
                <ul>
                    <li>10 free wishes per month (forever!)</li>
                    <li>Special founding member pricing on upgrades</li>
                    <li>Priority support from our team</li>
                    <li>Influence on future features</li>
                </ul>

                <div style="text-align: center;">
                    <a href="{invite_link}" class="button">Claim Your Access</a>
                </div>

                <p style="margin-top: 30px;">
                    This link is unique to you. Click above to create your account and start making wishes!
                </p>
            </div>

            <div class="footer">
                <p>&copy; 2024 The Wish Machine. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            to_email=email,
            subject='Your Early Access to The Wish Machine is Ready!',
            html_content=html_content
        )

    def send_subscription_confirmation(self, email: str, tier: str, amount: float) -> bool:
        """
        Send subscription confirmation email.

        Args:
            email: Email address
            tier: Subscription tier (premium/unlimited)
            amount: Monthly amount

        Returns:
            True if sent successfully
        """
        tier_benefits = {
            'premium': ['100 wishes per month', 'Priority processing', 'Advanced analytics'],
            'unlimited': ['Unlimited wishes', 'Highest priority processing', 'Premium analytics', 'Early access to new features']
        }

        benefits = tier_benefits.get(tier, [])
        benefits_html = ''.join([f'<li>{benefit}</li>' for benefit in benefits])

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    padding: 40px 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 8px;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .content {{
                    padding: 20px;
                    background: #f9f9f9;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .tier-badge {{
                    display: inline-block;
                    padding: 8px 16px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 20px;
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 14px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">✨</div>
                <h1>Subscription Confirmed!</h1>
            </div>

            <div class="content">
                <p>Thank you for upgrading to <span class="tier-badge">{tier.upper()}</span></p>

                <p><strong>Your benefits:</strong></p>
                <ul>
                    {benefits_html}
                </ul>

                <p><strong>Billing:</strong> ${amount:.2f}/month</p>

                <p>You can manage your subscription anytime from your account settings.</p>

                <p style="margin-top: 30px;">
                    Ready to manifest your reality? Start making wishes now!
                </p>
            </div>

            <div class="footer">
                <p>&copy; 2024 The Wish Machine. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            to_email=email,
            subject=f'Welcome to The Wish Machine {tier.title()} Plan!',
            html_content=html_content
        )

    def notify_admin_new_waitlist(self, email: str, name: Optional[str] = None) -> bool:
        """
        Notify admin of new waitlist signup.

        Args:
            email: New signup email
            name: Optional name

        Returns:
            True if sent successfully
        """
        name_info = f' ({name})' if name else ''
        html_content = f"""
        <html>
        <body>
            <h2>New Waitlist Signup</h2>
            <p><strong>Email:</strong> {email}{name_info}</p>
            <p><strong>Time:</strong> {self._get_current_time()}</p>
        </body>
        </html>
        """

        return self.send_email(
            to_email=self.admin_email,
            subject=f'New Waitlist Signup: {email}',
            html_content=html_content
        )

    @staticmethod
    def _get_current_time() -> str:
        """Get current time as formatted string."""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')


# Global email service instance
email_service = EmailService()
