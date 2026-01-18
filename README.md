# README.md
"""
# HustleHawk Job Dashboard

Remote job aggregator dashboard deployed on Render.

## Features
- 📅 Date filters (Today, This Week, All Jobs)
- 🆕 Fresh job badges
- ⭐ Match scoring
- 🗑️ Auto-cleanup (7 day retention)

## Tech Stack
- Python (backend)
- SQLite (database)
- Vanilla JS (frontend)

## Deployment
This dashboard is deployed on Render's free tier.
Jobs are scraped locally and database is uploaded manually.

## Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Run server: `python dashboard_server.py`
3. Open: http://localhost:8000/dashboard.html
"""

# ============================================================================
# DEPLOYMENT INSTRUCTIONS
# ============================================================================

INSTRUCTIONS = """
🚀 RENDER DEPLOYMENT GUIDE

STEP 1: PREPARE FILES
----------------------
Create these files in your project folder:

1. render.yaml (see above)
2. requirements.txt (see above)
3. .gitignore (see above)
4. README.md (see above)
5. Make sure you have:
   - dashboard.html
   - dashboard_server.py (updated version above)
   - jobhunter.db (with jobs)

STEP 2: CREATE GITHUB REPO
---------------------------
git init
git add .
git commit -m "Initial commit - HustleHawk Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hustlehawk-dashboard.git
git push -u origin main

STEP 3: DEPLOY ON RENDER
-------------------------
1. Go to https://render.com
2. Sign up/Login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Configure:
   - Name: hustlehawk-dashboard
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: python dashboard_server.py
   - Plan: Free
6. Click "Create Web Service"

STEP 4: INITIAL DATABASE UPLOAD
--------------------------------
After first deployment:
1. Go to Render dashboard
2. Click on your service
3. Go to "Shell" tab
4. Upload jobhunter.db using their file upload feature

OR use render-cli:
render exec -s hustlehawk-dashboard
# Then upload db file

STEP 5: UPDATE JOBS (AFTER SCRAPING)
-------------------------------------
Every time you scrape new jobs locally:

1. Run scraper locally:
   python3 hustle_scraper.py

2. Upload new database to Render:
   - Option A: Use Render Shell (upload file manually)
   - Option B: Use render-cli to push db
   - Option C: Use GitHub (commit db, auto-redeploy)

RECOMMENDED: GitHub Auto-Deploy
--------------------------------
1. After local scrape, commit db:
   git add jobhunter.db
   git commit -m "Updated jobs - $(date)"
   git push

2. Render auto-deploys on push
3. Dashboard updates with new jobs

STEP 6: SHARE WITH GROUP
-------------------------
Your dashboard will be live at:
https://hustlehawk-dashboard.onrender.com

Share this link in WhatsApp group! 🦅

TIPS:
-----
- Free tier sleeps after 15min inactivity (first load takes 30-60s)
- Scrape 2x daily (8am & 6pm)
- Push to GitHub after each scrape
- Database updates automatically
- No cost, completely free!
"""

print(INSTRUCTIONS)
