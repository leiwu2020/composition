# Setup Guide for Authentication and Payments

This guide will help you set up user authentication and payment processing for the AI Article Generator.

## Prerequisites

1. **Stripe Account** (for payment processing)
   - Sign up at [https://stripe.com](https://stripe.com)
   - Get your API keys from the Stripe Dashboard

2. **Environment Variables**

Create a `.env` file in the project root with the following variables:

```env
# OpenAI API Key (already set)
OPENAI_API_KEY=your-openai-api-key-here

# Flask Secret Key (generate a random string)
SECRET_KEY=your-random-secret-key-here

# Database URL
# For development (SQLite):
DATABASE_URL=sqlite:///composition.db
# For production (PostgreSQL):
# DATABASE_URL=postgresql://user:password@host:port/database

# Stripe Keys (from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Optional: Stripe Price ID (if you create a Product in Stripe)
STRIPE_MONTHLY_PRICE_ID=price_your-price-id
```

## Stripe Setup Instructions

### 1. Get Stripe API Keys

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com)
2. Make sure you're in **Test Mode** (toggle in top right)
3. Go to **Developers** → **API keys**
4. Copy your **Publishable key** and **Secret key**
5. Add them to your `.env` file

### 2. Create a Product and Price (Optional)

1. In Stripe Dashboard, go to **Products**
2. Click **Add product**
3. Name: "AI Article Generator - Monthly Subscription"
4. Pricing model: **Recurring**
5. Price: $9.99 per month
6. Copy the Price ID and add to `.env` as `STRIPE_MONTHLY_PRICE_ID`

**Note:** If you don't set `STRIPE_MONTHLY_PRICE_ID`, the app will create prices dynamically.

### 3. Set Up Webhook (Important for Production)

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **Add endpoint**
3. Endpoint URL: `https://your-domain.com/payment/webhook`
4. Select events to listen to:
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copy the **Signing secret** and add to `.env` as `STRIPE_WEBHOOK_SECRET`

**For local testing**, use Stripe CLI:
```bash
stripe listen --forward-to localhost:5000/payment/webhook
```
This will give you a webhook secret that starts with `whsec_`

## Installation

1. **Install new dependencies:**
   ```bash
   conda activate composition
   pip install -r requirements.txt
   ```

2. **Initialize the database:**
   The database will be created automatically when you run the app for the first time.

3. **Generate a secret key:**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output and add it to `.env` as `SECRET_KEY`

## Running the Application

```bash
conda activate composition
python app.py
```

The application will:
- Create the database automatically
- Create all necessary tables
- Start the server on http://localhost:5000

## Testing the Payment Flow

### Test Cards (Stripe Test Mode)

Use these test card numbers:
- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- Any future expiration date
- Any 3-digit CVC
- Any ZIP code

### Testing Steps

1. Register a new account at `/auth/register`
2. Login at `/auth/login`
3. Go to `/payment/pricing`
4. Click "Subscribe Now"
5. Use test card: `4242 4242 4242 4242`
6. Complete checkout
7. You'll be redirected to dashboard showing active subscription

## Deployment Considerations

### Database
- For production, use PostgreSQL instead of SQLite
- Update `DATABASE_URL` in environment variables
- Render.com provides free PostgreSQL databases

### Security
- **Change `SECRET_KEY`** to a strong random string
- **Never commit** `.env` file to Git
- Use **Stripe Live keys** in production (not test keys)
- Enable HTTPS (most hosting providers do this automatically)

### Environment Variables in Production
Set these in your hosting platform (Render, Railway, etc.):
- `OPENAI_API_KEY`
- `SECRET_KEY`
- `DATABASE_URL` (PostgreSQL for production)
- `STRIPE_SECRET_KEY` (Live key)
- `STRIPE_PUBLISHABLE_KEY` (Live key)
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_MONTHLY_PRICE_ID` (optional)

## Current Features

✅ User registration and login
✅ Password hashing with bcrypt
✅ Session management with Flask-Login
✅ Stripe subscription payments
✅ Subscription status tracking
✅ Webhook handling for subscription updates
✅ Protected routes (require authentication + subscription)
✅ User dashboard for managing subscriptions

## Next Steps

1. Test the full flow locally
2. Set up Stripe webhook for production
3. Deploy to hosting platform
4. Configure production Stripe keys
5. Test payment flow in production

## Troubleshooting

**"No module named 'models'"**
- Make sure you're running from the project root directory

**Stripe errors:**
- Verify your Stripe keys are correct
- Make sure you're using test keys in development
- Check Stripe Dashboard for error logs

**Database errors:**
- Delete `composition.db` and restart the app to recreate it
- Check that SQLite is installed

**Import errors:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`

