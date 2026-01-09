# Stripe API Key Configuration

## Current Setup

The Stripe API key has been saved to the `.env` file and is automatically loaded by the application.

### Key Information

- **Key Type:** Restricted Key (rk_test_)
- **Environment Variable:** `STRIPE_SECRET_KEY`
- **Location:** `.env` file (not committed to Git)

### How It Works

1. The `.env` file is loaded automatically by `app.py` using `python-dotenv`
2. The `payments.py` module reads the key using `os.getenv('STRIPE_SECRET_KEY')`
3. Stripe is initialized with: `stripe.api_key = os.getenv('STRIPE_SECRET_KEY')`

### Restricted Keys

The key provided starts with `rk_test_` which is a **Restricted Key**. These keys have limited permissions compared to standard secret keys (`sk_test_`). 

**Important Notes:**
- Restricted keys are safer as they have limited scope
- Make sure the key has the necessary permissions for:
  - Creating customers
  - Creating subscriptions
  - Managing checkout sessions
  - Webhook handling

### Testing

To verify the key is loaded correctly:

```bash
conda activate composition
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key loaded:', 'Yes' if os.getenv('STRIPE_SECRET_KEY') else 'No')"
```

### Security

- ✅ `.env` file is in `.gitignore` (not committed to Git)
- ✅ Key is only loaded from environment variables
- ✅ Never commit API keys to version control

### Adding Publishable Key

If you have a Stripe Publishable Key (starts with `pk_test_`), add it to `.env`:

```bash
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

This is used for the frontend Stripe Checkout integration.

