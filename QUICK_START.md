# Quick Start Guide - Authentication & Payments

## What's Been Added

✅ User registration and login system
✅ Monthly subscription payment ($9.99/month)
✅ Stripe payment integration
✅ User dashboard
✅ Protected routes (require login + active subscription)

## Quick Setup Steps

### 1. Install New Dependencies

```bash
conda activate composition
pip install -r requirements.txt
```

### 2. Set Up Stripe Account

1. **Create Stripe Account:**
   - Go to https://stripe.com and sign up
   - You'll get test mode keys automatically

2. **Get Your API Keys:**
   - Dashboard → Developers → API keys
   - Copy **Publishable key** and **Secret key** (test mode)

3. **Create Environment Variables:**
   ```bash
   # Generate a secret key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Create/update `.env` file:
   ```env
   OPENAI_API_KEY=your-openai-key
   SECRET_KEY=paste-generated-secret-key-here
   DATABASE_URL=sqlite:///composition.db
   STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
   STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
   STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret (optional for now)
   ```

### 3. Run the Application

```bash
conda activate composition
python app.py
```

### 4. Test the Flow

1. **Register:** Go to http://localhost:5000/auth/register
2. **Login:** Go to http://localhost:5000/auth/login
3. **Subscribe:** Go to http://localhost:5000/payment/pricing
4. **Test Payment:** Use card `4242 4242 4242 4242` (Stripe test card)
5. **Dashboard:** View your subscription at http://localhost:5000/payment/dashboard

## Test Card Numbers

- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- Use any future expiry date, any CVC, any ZIP

## Key Routes

- `/` - Main article generator (requires login + subscription)
- `/auth/register` - User registration
- `/auth/login` - User login
- `/auth/logout` - Logout
- `/payment/pricing` - View pricing and subscribe
- `/payment/dashboard` - Manage subscription
- `/payment/webhook` - Stripe webhook endpoint

## Important Notes

⚠️ **For Production:**
- Change `SECRET_KEY` to a strong random value
- Use Stripe **Live keys** (not test keys)
- Set up webhook endpoint in Stripe Dashboard
- Use PostgreSQL instead of SQLite
- Enable HTTPS (automatic on most hosting platforms)

## Deployment

When deploying to Render/Railway/etc., make sure to set all environment variables in the hosting platform's dashboard.

See `SETUP.md` for detailed instructions.

