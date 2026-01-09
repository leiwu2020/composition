# Test Accounts Login Guide

## Quick Login Instructions

### Step 1: Access the Login Page

1. Open your web browser
2. Navigate to: **http://localhost:5000/auth/login**
   - Or click "Login" from the homepage if the server is running

### Step 2: Enter Credentials

Use one of the following test accounts:

## Test Accounts

| Username | Password | Plan | Query Limit |
|----------|----------|------|-------------|
| **TestA** | test123 | Free | 3 queries/month |
| **TestB** | test123 | Basic | 3 queries/week |
| **TestC** | test123 | Elite | 10 queries/day |
| **TestD** | test123 | Advanced | 100 queries/month |
| **TestE** | test123 | Annual | 100 queries/month |

### All accounts use the same password: `test123`

## Login Steps

1. **Go to Login Page**
   - URL: http://localhost:5000/auth/login
   - Or click "Login" link from homepage

2. **Enter Username**
   - Type: `TestA`, `TestB`, `TestC`, `TestD`, or `TestE`

3. **Enter Password**
   - Type: `test123`

4. **Click "Login" button**

5. **You'll be redirected to the homepage**
   - You'll see your username and plan info in the header
   - Remaining queries will be displayed

## Testing Different Plans

### TestA (Free Plan)
- **Limit:** 3 queries per month
- **Test:** Try generating 4 articles - the 4th should be blocked

### TestB (Basic Plan)
- **Limit:** 3 queries per week
- **Test:** Generate 3 articles, then try a 4th - should be blocked until next week

### TestC (Elite Plan)
- **Limit:** 10 queries per day
- **Test:** Generate 10 articles, then try an 11th - should be blocked until next day

### TestD (Advanced Plan)
- **Limit:** 100 queries per month
- **Test:** Generate multiple articles throughout the month

### TestE (Annual Plan)
- **Limit:** 100 queries per month
- **Test:** Same as Advanced, but with annual billing

## Viewing Account Info

After logging in:
- **Homepage:** Shows plan name and remaining queries in header
- **Dashboard:** Go to http://localhost:5000/payment/dashboard
  - Shows detailed account information
  - Current plan
  - Remaining queries
  - Subscription details

## Quick Access URLs

- **Login:** http://localhost:5000/auth/login
- **Register:** http://localhost:5000/auth/register
- **Homepage:** http://localhost:5000
- **Dashboard:** http://localhost:5000/payment/dashboard
- **Pricing:** http://localhost:5000/payment/pricing

## Troubleshooting

**Can't login?**
- Make sure the server is running: `python app.py`
- Check that you're using the correct username (case-sensitive)
- Verify password is `test123` (all lowercase)

**Account not found?**
- Run the setup script: `python create_test_accounts.py`
- This will create all test accounts if they don't exist

**Want to test query limits?**
- Login with TestA (Free plan)
- Generate 3 articles
- Try to generate a 4th - you should see an error message about query limit

