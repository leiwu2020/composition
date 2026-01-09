# Deployment Guide

This guide will help you deploy the AI Article Generator to a free hosting service and set up a free domain.

## Option 1: Render.com (Recommended - Easiest)

### Step 1: Push Code to GitHub
Make sure your code is pushed to GitHub (already done if you followed the commit steps).

### Step 2: Deploy on Render

1. **Sign up for Render:**
   - Go to [https://render.com](https://render.com)
   - Sign up with your GitHub account (free)

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `leiwu2020/composition`
   - Configure settings:
     - **Name:** `composition-app` (or any name you like)
     - **Region:** Choose closest to you
     - **Branch:** `Master`
     - **Root Directory:** (leave empty)
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`

3. **Environment Variables:**
   - Click "Environment" tab
   - Add: `OPENAI_API_KEY` = `your-openai-api-key`
   - Add: `PORT` = `10000` (Render automatically sets this, but just in case)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically deploy your app
   - You'll get a free subdomain like: `composition-app.onrender.com`

### Step 3: Get a Free Custom Domain (Optional)

**Option A: Use Render's Free Subdomain** (Already included)
- Your app will be available at: `composition-app.onrender.com`
- No additional setup needed

**Option B: Free Domain from Freenom** (Advanced)
- Go to [https://freenom.com](https://freenom.com)
- Search for available free domains (.tk, .ml, .ga, .cf, .gq)
- Register a free domain
- In Render dashboard → Settings → Custom Domains
- Add your domain and follow DNS configuration instructions

**Option C: DuckDNS** (Free Subdomain)
- Go to [https://www.duckdns.org](https://www.duckdns.org)
- Create a free subdomain (e.g., `composition.duckdns.org`)
- Use Render's custom domain feature to point to it

## Option 2: Railway.app (Alternative)

### Step 1: Deploy on Railway

1. **Sign up:**
   - Go to [https://railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `leiwu2020/composition`

3. **Configure:**
   - Railway auto-detects Python apps
   - Add environment variable: `OPENAI_API_KEY`
   - Railway will auto-deploy

4. **Get Domain:**
   - Railway provides a free subdomain automatically
   - Access your app at: `composition-production.up.railway.app` (or similar)

### Step 2: Custom Domain (Optional)
- In Railway dashboard → Settings → Domains
- Add custom domain (requires DNS configuration)

## Option 3: Fly.io (Alternative)

### Deploy on Fly.io

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Launch App:**
   ```bash
   fly launch
   ```
   - Follow prompts
   - It will create a `fly.toml` config file

4. **Set Secrets:**
   ```bash
   fly secrets set OPENAI_API_KEY=your-api-key-here
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

## Important Notes

### Environment Variables
Make sure to set `OPENAI_API_KEY` in your hosting platform's environment variables section. **Never commit your API key to GitHub!**

### Free Tier Limitations
- **Render:** Free tier spins down after 15 minutes of inactivity (first request may be slow)
- **Railway:** Limited free credits per month
- **Fly.io:** Free tier has resource limits

### Custom Domain Setup
Most free domains require:
1. DNS configuration to point to your hosting provider
2. SSL certificate setup (usually automatic on these platforms)
3. Wait 24-48 hours for DNS propagation

## Troubleshooting

### App Not Starting
- Check logs in your hosting platform dashboard
- Verify `OPENAI_API_KEY` is set correctly
- Ensure `gunicorn` is in requirements.txt
- Check that port is configured correctly

### Domain Not Working
- Verify DNS settings are correct
- Wait for DNS propagation (can take up to 48 hours)
- Check SSL certificate status in hosting dashboard

## Updating Your App

After making changes:
1. Commit changes: `git add . && git commit -m "Your message"`
2. Push to GitHub: `git push origin Master`
3. Your hosting platform will automatically redeploy (if auto-deploy is enabled)

## Recommended Setup

For easiest deployment, I recommend:
1. **Deploy to Render.com** (simplest setup)
2. **Use Render's free subdomain** (no DNS configuration needed)
3. **Upgrade to custom domain later** if needed

This gives you a working deployment in minutes with zero cost!

