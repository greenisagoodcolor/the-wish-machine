"""
Temporary admin routes for viewing email signups
"""

from flask import Blueprint, jsonify, render_template_string
from models import EmailSubscriber, Waitlist, db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/email-signups')
def email_signups():
    """View all email signups"""

    # Get all email subscribers
    subscribers = EmailSubscriber.query.order_by(EmailSubscriber.created_at.desc()).all()

    # Get all waitlist entries
    waitlist_entries = Waitlist.query.order_by(Waitlist.created_at.desc()).all()

    # Get stats
    total_subs = db.session.query(func.count(EmailSubscriber.id)).scalar()
    active_subs = db.session.query(func.count(EmailSubscriber.id)).filter(
        EmailSubscriber.status == 'active'
    ).scalar()
    confirmed_subs = db.session.query(func.count(EmailSubscriber.id)).filter(
        EmailSubscriber.confirmed == True
    ).scalar()

    modal_subs = db.session.query(func.count(EmailSubscriber.id)).filter(
        EmailSubscriber.source == 'post_wish_modal'
    ).scalar()

    email_bar_subs = db.session.query(func.count(EmailSubscriber.id)).filter(
        EmailSubscriber.source == 'main_email_bar'
    ).scalar()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Signups - The Wish Machine Admin</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            h1 {
                margin-bottom: 10px;
                font-size: 36px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.15);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
            }
            .stat-label {
                font-size: 14px;
                opacity: 0.8;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .stat-value {
                font-size: 32px;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                overflow: hidden;
            }
            th {
                background: rgba(255, 255, 255, 0.2);
                padding: 15px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            tr:hover {
                background: rgba(255, 255, 255, 0.05);
            }
            .section {
                margin: 40px 0;
            }
            .section-title {
                font-size: 24px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
            }
            .badge-active { background: #4ade80; color: #064e3b; }
            .badge-pending { background: #fbbf24; color: #78350f; }
            .badge-confirmed { background: #60a5fa; color: #1e3a8a; }
            .badge-yes { background: #34d399; color: #064e3b; }
            .badge-no { background: #f87171; color: #7f1d1d; }
            .empty {
                text-align: center;
                padding: 40px;
                opacity: 0.6;
                font-style: italic;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Email Signups Admin</h1>
            <p style="opacity: 0.8; margin-bottom: 30px;">Real-time view of all email subscribers and waitlist entries</p>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-label">Total Subscribers</div>
                    <div class="stat-value">{{ total_subs }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Active</div>
                    <div class="stat-value">{{ active_subs }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Confirmed</div>
                    <div class="stat-value">{{ confirmed_subs }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">From Modal</div>
                    <div class="stat-value">{{ modal_subs }}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">From Email Bar</div>
                    <div class="stat-value">{{ email_bar_subs }}</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">📬 Email Subscribers ({{ subscribers|length }})</h2>
                {% if subscribers %}
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Email</th>
                            <th>Source</th>
                            <th>Status</th>
                            <th>Confirmed</th>
                            <th>Wish Mates</th>
                            <th>Tips</th>
                            <th>Education</th>
                            <th>Signed Up</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for sub in subscribers %}
                        <tr>
                            <td>{{ sub.id }}</td>
                            <td><strong>{{ sub.email }}</strong></td>
                            <td>{{ sub.source or 'unknown' }}</td>
                            <td><span class="badge badge-{{ sub.status }}">{{ sub.status }}</span></td>
                            <td>
                                {% if sub.confirmed %}
                                <span class="badge badge-yes">✓</span>
                                {% else %}
                                <span class="badge badge-no">✗</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if sub.wants_wish_mates %}
                                <span class="badge badge-yes">✓</span>
                                {% else %}
                                <span class="badge badge-no">✗</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if sub.wants_tips %}
                                <span class="badge badge-yes">✓</span>
                                {% else %}
                                <span class="badge badge-no">✗</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if sub.wants_education %}
                                <span class="badge badge-yes">✓</span>
                                {% else %}
                                <span class="badge badge-no">✗</span>
                                {% endif %}
                            </td>
                            <td>{{ sub.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty">No email subscribers yet</div>
                {% endif %}
            </div>

            <div class="section">
                <h2 class="section-title">📝 Waitlist Entries ({{ waitlist_entries|length }})</h2>
                {% if waitlist_entries %}
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Email</th>
                            <th>Name</th>
                            <th>Source</th>
                            <th>Status</th>
                            <th>Signed Up</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for entry in waitlist_entries %}
                        <tr>
                            <td>{{ entry.id }}</td>
                            <td><strong>{{ entry.email }}</strong></td>
                            <td>{{ entry.name or '-' }}</td>
                            <td>{{ entry.source or 'unknown' }}</td>
                            <td><span class="badge badge-{{ entry.status }}">{{ entry.status }}</span></td>
                            <td>{{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty">No waitlist entries yet</div>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html,
        subscribers=subscribers,
        waitlist_entries=waitlist_entries,
        total_subs=total_subs,
        active_subs=active_subs,
        confirmed_subs=confirmed_subs,
        modal_subs=modal_subs,
        email_bar_subs=email_bar_subs
    )


@admin_bp.route('/email-signups/json')
def email_signups_json():
    """Get email signups as JSON"""
    subscribers = EmailSubscriber.query.order_by(EmailSubscriber.created_at.desc()).all()

    return jsonify({
        'subscribers': [
            {
                'id': s.id,
                'email': s.email,
                'source': s.source,
                'status': s.status,
                'confirmed': s.confirmed,
                'wants_wish_mates': s.wants_wish_mates,
                'wants_tips': s.wants_tips,
                'wants_education': s.wants_education,
                'created_at': s.created_at.isoformat()
            }
            for s in subscribers
        ]
    })
