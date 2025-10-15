# The Wish Machine

A beautiful web application that uses quantum consciousness theory to influence reality collapse. Make wishes, track manifestation probabilities, and explore the intersection of consciousness and quantum mechanics.

## Features

- **Quantum Wish Simulation**: Run 1000 quantum collapse simulations per wish
- **User Authentication**: Secure signup, login, and session management
- **Subscription Tiers**: Free, Premium ($9.99/mo), and Unlimited ($29.99/mo) plans
- **Payment Integration**: Stripe-powered subscription management
- **Waitlist System**: Email collection with automated notifications
- **Usage Tracking**: Monitor wishes per month with tier-based limits
- **Wish History**: Track all your past wishes and their outcomes
- **Email Notifications**: SendGrid integration for transactional emails
- **Production Ready**: Docker, Gunicorn, PostgreSQL, Redis

## Tech Stack

- **Backend**: Flask (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Rate Limiting**: Redis
- **Payment Processing**: Stripe
- **Email Service**: SendGrid
- **Authentication**: Flask-Login + bcrypt
- **Production Server**: Gunicorn
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Stripe account
- SendGrid account

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd choicemaker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Initialize database**
   ```bash
   python app.py
   # Or use Flask CLI:
   flask init-db
   ```

6. **Run development server**
   ```bash
   python app.py
   # Or:
   flask run --host=0.0.0.0 --port=8080
   ```

Visit `http://localhost:8080`

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database (first time only)**
   ```bash
   docker-compose exec app flask init-db
   ```

3. **View logs**
   ```bash
   docker-compose logs -f app
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

#### Flask Settings
- `FLASK_APP`: Application entry point (default: `app.py`)
- `FLASK_ENV`: Environment (`development` or `production`)
- `SECRET_KEY`: Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)

#### Database
- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://wishuser:password@localhost:5432/wishmachine`

#### Stripe
- `STRIPE_PUBLIC_KEY`: Your Stripe publishable key
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: Webhook signing secret
- `STRIPE_PRICE_ID_PREMIUM`: Price ID for Premium tier
- `STRIPE_PRICE_ID_UNLIMITED`: Price ID for Unlimited tier

#### SendGrid
- `SENDGRID_API_KEY`: Your SendGrid API key
- `SENDGRID_FROM_EMAIL`: From email address
- `ADMIN_EMAIL`: Admin notification email

#### Application Settings
- `MAX_WISHES_FREE`: Free tier monthly limit (default: 10)
- `MAX_WISHES_PREMIUM`: Premium tier monthly limit (default: 100)
- `MAX_WISHES_UNLIMITED`: Unlimited tier limit (default: 999999)

### Stripe Setup

1. **Create a Stripe account** at [stripe.com](https://stripe.com)

2. **Create Products and Prices**
   - Go to Products → Add Product
   - Create "Premium" plan: $9.99/month recurring
   - Create "Unlimited" plan: $29.99/month recurring
   - Copy the Price IDs to your `.env` file

3. **Set up Webhook**
   - Go to Developers → Webhooks → Add Endpoint
   - URL: `https://yourdomain.com/webhook`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
   - Copy the webhook signing secret to `.env`

### SendGrid Setup

1. **Create SendGrid account** at [sendgrid.com](https://sendgrid.com)

2. **Create API Key**
   - Go to Settings → API Keys → Create API Key
   - Give it "Full Access" permission
   - Copy to `.env` as `SENDGRID_API_KEY`

3. **Verify sender identity**
   - Go to Settings → Sender Authentication
   - Verify your sending email address
   - Use this as `SENDGRID_FROM_EMAIL` in `.env`

## Database Migrations

Using Flask-Migrate (Alembic):

```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

## Deployment Options

### Option 1: Railway.app (Recommended for Quick Deploy)

1. **Create Railway account** at [railway.app](https://railway.app)
2. **Create new project** → Deploy from GitHub
3. **Add PostgreSQL database** (automatically configured)
4. **Add Redis** (automatically configured)
5. **Set environment variables** from `.env.example`
6. **Deploy!**

Railway will automatically:
- Detect the Dockerfile
- Build and deploy your app
- Provide a public URL
- Handle SSL certificates

### Option 2: Render.com

1. **Create account** at [render.com](https://render.com)
2. **Create PostgreSQL database**
3. **Create Redis instance**
4. **Create Web Service**:
   - Environment: Docker
   - Build command: (automatic)
   - Start command: (automatic from Dockerfile)
5. **Add environment variables**
6. **Deploy**

### Option 3: DigitalOcean App Platform

1. **Create DO account**
2. **App Platform** → Create App → From GitHub
3. **Add components**:
   - Web Service (auto-detected from Dockerfile)
   - Managed PostgreSQL Database
   - Managed Redis Database
4. **Configure environment variables**
5. **Deploy**

### Option 4: Self-Hosted (VPS/Cloud)

```bash
# On your server
git clone <your-repo>
cd choicemaker

# Create .env file with production values
nano .env

# Run with Docker Compose
docker-compose up -d

# Set up reverse proxy (nginx example)
# Add SSL with Let's Encrypt
```

## Testing

### Run Type Checking (mypy)

```bash
mypy --verbose --show-traceback --show-error-context --show-column-numbers \
     --show-error-codes --pretty --show-absolute-path --no-incremental \
     --no-cache-dir app.py models.py auth.py payments.py email_service.py
```

### Run Linting (flake8)

```bash
flake8 -vv --show-source --statistics --count --benchmark \
       --format='%(path)s:%(row)d:%(col)d: [%(code)s] %(text)s' \
       app.py models.py auth.py payments.py email_service.py
```

## Project Structure

```
choicemaker/
├── app.py                  # Main Flask application
├── models.py               # Database models (User, Waitlist, Wish, Payment)
├── auth.py                 # Authentication routes and logic
├── payments.py             # Stripe integration and payment handling
├── email_service.py        # SendGrid email service
├── choicemaker.py          # Quantum collapse simulation
├── quantum_state.py        # Quantum state definitions
├── gunicorn_config.py      # Gunicorn production configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container orchestration
├── .env.example            # Environment variables template
├── templates/              # HTML templates
│   ├── index.html          # Main wish-making interface
│   ├── landing.html        # Public landing page
│   ├── waitlist.html       # Waitlist signup
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── pricing.html        # Pricing tiers
│   ├── account.html        # User account management
│   └── wishes_history.html # Wish history
└── migrations/             # Database migrations (auto-generated)
```

## API Endpoints

### Public Endpoints
- `GET /` - Landing page (or app if logged in)
- `GET /waitlist` - Waitlist signup form
- `POST /waitlist` - Submit waitlist signup
- `POST /api/waitlist` - API waitlist signup
- `GET /pricing` - Pricing page
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /signup` - Signup page
- `POST /signup` - Process signup

### Authenticated Endpoints
- `GET /app` - Main wish-making interface
- `POST /make_wish` - Submit a wish (rate limited: 30/hour)
- `GET /my-wishes` - View wish history
- `GET /account` - Account settings
- `GET /logout` - Logout

### Payment Endpoints
- `GET /subscribe/<tier>` - Create Stripe checkout session
- `GET /subscription/success` - Post-checkout success page
- `GET /manage-subscription` - Stripe customer portal
- `POST /webhook` - Stripe webhook handler

## Pricing Tiers

| Feature | Free | Premium | Unlimited |
|---------|------|---------|-----------|
| **Price** | $0 | $9.99/mo | $29.99/mo |
| **Wishes/Month** | 10 | 100 | Unlimited |
| **Processing** | Standard | Priority | Highest Priority |
| **Analytics** | Basic | Advanced | Premium Dashboard |
| **History** | Last 30 days | Unlimited | Unlimited |
| **Support** | Community | Email | Priority Email + Chat |
| **API Access** | No | No | Coming Soon |

## Security Considerations

- **Passwords**: Hashed with bcrypt
- **Sessions**: Secure session cookies with Flask-Login
- **Rate Limiting**: Implemented with Flask-Limiter
- **CSRF Protection**: Flask-WTF forms
- **SQL Injection**: Protected by SQLAlchemy ORM
- **Environment Variables**: Never commit `.env` to git
- **Stripe Webhooks**: Signature verification required
- **Production**: Always use HTTPS in production

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps db

# View database logs
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Migration Issues
```bash
# Reset migrations
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade
```

## Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo/issues]
- Email: [your-email]
- Documentation: [your-docs-url]

## License

[Your License Here]

## Credits

Built with consciousness-influenced quantum mechanics. Powered by Python, Flask, Stripe, and a bit of universal magic.
