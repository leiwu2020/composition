# Subscription Plans

## Available Plans

### 1. Free Plan
- **Price:** $0/month
- **Queries:** 3 queries per month
- **Features:**
  - AI-powered article generation
  - All languages supported
  - Multiple download formats (TXT, DOC, PDF, HTML)
  - Chinese Pinyin support
  - Language level selection

### 2. Basic Plan
- **Price:** $4.99/month
- **Queries:** 3 queries per week
- **Features:**
  - All Free plan features
  - Priority support
  - Cancel anytime

### 3. Elite Plan (Most Popular)
- **Price:** $9.99/month
- **Queries:** 10 queries per day
- **Features:**
  - All Basic plan features
  - Higher daily query limit
  - Best value for regular users

### 4. Advanced Plan
- **Price:** $19.99/month
- **Queries:** 100 queries per month
- **Features:**
  - All Elite plan features
  - High monthly query limit
  - Perfect for power users

### 5. Annual Pass
- **Price:** $199.99/year (Save ~17% vs monthly)
- **Queries:** 100 queries per month
- **Features:**
  - All Advanced plan features
  - Best value for long-term users
  - Annual billing

## Query Limits

Query limits are enforced based on the plan type:
- **Daily limits:** Reset at midnight UTC
- **Weekly limits:** Reset on Monday at midnight UTC
- **Monthly limits:** Reset on the 1st of each month at midnight UTC

## Test Accounts

For testing purposes, the following accounts have been created:

| Username | Plan | Password | Queries |
|----------|------|----------|---------|
| TestA | Free | test123 | 3/month |
| TestB | Basic | test123 | 3/week |
| TestC | Elite | test123 | 10/day |
| TestD | Advanced | test123 | 100/month |
| TestE | Annual | test123 | 100/month |

## Usage Tracking

All queries are logged in the database. Users can see their remaining queries:
- On the homepage (header)
- On the dashboard page
- In API responses after generating articles

## Upgrading Plans

Users can upgrade their plan at any time by:
1. Going to `/payment/pricing`
2. Selecting a new plan
3. Completing payment through Stripe

The new plan will be activated immediately, and query limits will reset based on the new plan's period.

