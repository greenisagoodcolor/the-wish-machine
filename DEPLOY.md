# Quick Deployment Guide for The Wish Machine

## Fastest Path to Production

### Option 1: Railway.app (5 minutes)

**Best for**: Quick deploy with zero config

1. **Create account** at [railway.app](https://railway.app)
2. **Click "New Project" → "Deploy from GitHub"**
3. **Add services**:
   - PostgreSQL (click "Add Service" → "Database" → "PostgreSQL")
   - Redis (click "Add Service" → "Database" → "Redis")
4. **Set environment variables** in your app service:
   ```
   Copy all from .env.example and fill in:
   - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
   - DATABASE_URL (auto-filled by Railway)
   - RATELIMIT_STORAGE_URL (auto-filled by Railway)
   - STRIPE_PUBLIC_KEY (from Stripe dashboard)
   - STRIPE_SECRET_KEY (from Stripe dashboard)
   - STRIPE_WEBHOOK_SECRET (from Stripe webhooks)
   - STRIPE_PRICE_ID_PREMIUM (create in Stripe)
   - STRIPE_PRICE_ID_UNLIMITED (create in Stripe)
   - SENDGRID_API_KEY (from SendGrid)
   - SENDGRID_FROM_EMAIL (your verified email)
   ```
5. **Deploy!** - Railway auto-deploys from main branch

**URL**: Railway provides `https://yourapp.railway.app`

---

### Option 2: Render.com (10 minutes)

**Best for**: Free tier with great UX

1. **Create account** at [render.com](https://render.com)
2. **Create PostgreSQL**:
   - New → PostgreSQL
   - Name: wishmachine-db
   - Free tier
3. **Create Redis**:
   - New → Redis
   - Name: wishmachine-redis
   - Free tier
4. **Create Web Service**:
   - New → Web Service
   - Connect your GitHub repo
   - Environment: Docker
   - Instance Type: Free (or Starter $7/mo)
5. **Add environment variables** (same as Railway above, but manually set DATABASE_URL from Postgres internal URL)
6. **Deploy!**

**URL**: `https://yourapp.onrender.com`

---

### Option 3: DigitalOcean App Platform (15 minutes)

**Best for**: Production-ready, scalable

1. **Create account** at [digitalocean.com](https://digitalocean.com)
2. **Apps → Create App → GitHub**
3. **Add components**:
   - Web Service (auto-detected)
   - Dev Database → PostgreSQL ($7/mo)
   - Dev Database → Redis ($7/mo)
4. **Environment variables** (same as above)
5. **Choose plan**: Basic $5/mo or Professional $12/mo
6. **Deploy!**

**URL**: `https://yourapp.ondigitalocean.app` (can add custom domain)

---

## Pre-Deployment Checklist

### 1. Stripe Setup (15 minutes)

1. **Create Stripe account**: [dashboard.stripe.com/register](https://dashboard.stripe.com/register)

2. **Create Products**:
   - Go to Products → Add Product
   - **Premium Plan**:
     - Name: "Premium"
     - Price: $9.99/month recurring
     - Copy Price ID → `STRIPE_PRICE_ID_PREMIUM`
   - **Unlimited Plan**:
     - Name: "Unlimited"
     - Price: $29.99/month recurring
     - Copy Price ID → `STRIPE_PRICE_ID_UNLIMITED`

3. **Get API Keys**:
   - Go to Developers → API Keys
   - Copy "Publishable key" → `STRIPE_PUBLIC_KEY`
   - Copy "Secret key" → `STRIPE_SECRET_KEY`

4. **Set up Webhook** (after deployment):
   - Go to Developers → Webhooks → Add Endpoint
   - URL: `https://yourdomain.com/webhook`
   - Events: Select all `checkout.*`, `customer.subscription.*`, `invoice.*`
   - Copy "Signing secret" → `STRIPE_WEBHOOK_SECRET`

### 2. SendGrid Setup (10 minutes)

1. **Create SendGrid account**: [signup.sendgrid.com](https://signup.sendgrid.com)

2. **Create API Key**:
   - Settings → API Keys → Create API Key
   - Name: "WishMachine Production"
   - Permissions: Full Access
   - Copy key → `SENDGRID_API_KEY`

3. **Verify Sender**:
   - Settings → Sender Authentication → Single Sender Verification
   - Add your email → Verify
   - Use this email for `SENDGRID_FROM_EMAIL`

### 3. Environment Variables

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Post-Deployment Steps

### 1. Initialize Database

**Railway/Render/DigitalOcean**:
```bash
# SSH into your service or use the web console
flask db upgrade  # Run migrations

# Or with Docker
docker-compose exec app flask db upgrade
```

### 2. Create Admin User

```bash
flask create-admin
# Enter email and password when prompted
```

### 3. Test the Application

1. **Visit your app URL**
2. **Sign up for waitlist** → Check you receive email
3. **Create account** → Test login
4. **Make a wish** → Verify it works
5. **Test Stripe** (use test mode):
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVC: Any 3 digits

### 4. Configure Custom Domain (Optional)

**Railway**: Settings → Domains → Add Domain
**Render**: Settings → Custom Domain
**DigitalOcean**: Settings → Domains

Add DNS records:
```
CNAME @ your-app-url.platform.app
```

---

## Monitoring & Maintenance

### View Logs

**Railway**: Click on service → Logs tab
**Render**: Dashboard → Logs
**DigitalOcean**: App → Runtime Logs

### Database Backups

All platforms provide automatic backups. Configure:
- **Railway**: Automatic for paid plans
- **Render**: Daily backups on paid plans
- **DigitalOcean**: Automatic daily backups

### Scaling

Start small, scale as needed:
- **Free tier**: Good for 100-1000 users
- **$5-12/mo**: Good for 1000-10000 users
- **$25+/mo**: 10000+ users

Monitor:
- Database connections
- Redis memory
- API response times
- Stripe webhook success rate

---

## Troubleshooting

### App won't start
- Check logs for errors
- Verify all environment variables are set
- Ensure DATABASE_URL is correct

### Stripe webhooks failing
- Check webhook signing secret matches
- Verify endpoint URL is correct (https)
- Check webhook event types are selected

### Emails not sending
- Verify SENDGRID_API_KEY is correct
- Check sender email is verified
- Look for rate limiting (SendGrid free tier: 100/day)

### Database connection errors
- Check DATABASE_URL format
- Verify database is running
- Check connection limits

---

## Cost Estimate

### Minimal Setup (Free - $15/mo)
- **Railway Free**: $0 (500hrs/mo free)
- **Render Free**: $0 (limited)
- **SendGrid**: $0 (100 emails/day)
- **Stripe**: $0 + 2.9% + $0.30 per transaction

### Production Setup ($25-50/mo)
- **Railway Pro**: $5-20/mo
- **PostgreSQL**: Included or $7/mo
- **Redis**: Included or $7/mo
- **SendGrid Essentials**: $20/mo (50k emails)
- **Stripe**: 2.9% + $0.30 per transaction
- **Domain**: $12/year

---

## Next Steps

1. ✅ Choose deployment platform
2. ✅ Set up Stripe account
3. ✅ Set up SendGrid account
4. ✅ Deploy application
5. ✅ Configure webhooks
6. ✅ Test end-to-end
7. ✅ Add custom domain
8. ✅ Launch!

Need help? Check the main README.md for detailed documentation.
