# Stripe API Key Loading Fix

## Issue
When users tried to upgrade their plan, they received an error:
```
Error: Error creating checkout session: No API key provided. 
(HINT: set your API key using "stripe.api_key = <API-KEY>")
```

## Root Cause
The Stripe API key was not being loaded properly when the `payments.py` module was imported. The `.env` file was being loaded in `app.py`, but `payments.py` was trying to access the key before the environment variables were loaded.

## Solution
1. **Added `load_dotenv()` to payments.py**: The module now loads the `.env` file at the top before initializing Stripe.

2. **Added error checking**: Before making any Stripe API calls, the code now verifies that the API key is set.

3. **Added fallback mechanism**: If the key is not set when a function is called, it attempts to reload it from the environment.

## Changes Made

### payments.py
- Added `from dotenv import load_dotenv` import
- Added `load_dotenv()` call at module level
- Added key verification before Stripe API calls
- Added error messages if key is missing

## Testing
✅ Stripe key now loads correctly when module is imported
✅ Key is verified before making API calls
✅ Error messages are clear if key is missing

## Verification
To verify the fix is working:

1. Check that the key loads:
   ```bash
   python -c "from payments import payments_bp; import stripe; print('Key set:', bool(stripe.api_key))"
   ```

2. Test plan upgrade in the dashboard
3. Should no longer see "No API key provided" error

## Notes
- The Stripe key is stored in `.env` file (not committed to Git)
- Key is automatically loaded when the application starts
- If you see the error again, check that `.env` file exists and contains `STRIPE_SECRET_KEY`

