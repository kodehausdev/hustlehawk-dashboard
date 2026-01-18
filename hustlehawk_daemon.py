import time
import json
import os
from datetime import datetime
import requests
from your_scraper_file import run_all_scrapers  # Import your main scraper

# === NOTIFICATION SETTINGS ===
NOTIFICATION_METHOD = "discord"  # Options: discord, email, telegram
DISCORD_WEBHOOK = "YOUR_DISCORD_WEBHOOK_URL"  # Get from Discord server settings
CHECK_INTERVAL = 3600  # Check every hour (in seconds)

# Store seen job IDs
SEEN_JOBS_FILE = "seen_jobs.json"

def load_seen_jobs():
    """Load previously seen job IDs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen_jobs):
    """Save seen job IDs"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)

def send_discord_notification(new_jobs):
    """Send notification to Discord"""
    if not new_jobs:
        return
    
    message = f"🦅 **HUSTLEHAWK ALERT** - {len(new_jobs)} NEW JOBS!\n\n"
    
    for job in new_jobs[:5]:  # Show top 5
        message += f"**{job['title']}** at {job['company']}\n"
        message += f"Match: {job['score']}% | {job['url']}\n\n"
    
    if len(new_jobs) > 5:
        message += f"_+ {len(new_jobs) - 5} more jobs. Check your dashboard!_"
    
    payload = {"content": message}
    
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
        print(f"✓ Sent Discord notification for {len(new_jobs)} jobs")
    except Exception as e:
        print(f"✗ Discord notification failed: {e}")

def get_new_jobs_from_db():
    """Get jobs from your database that haven't been seen yet"""
    # Adjust this based on how your save_to_db works
    # This is a placeholder - you'll need to query your actual DB
    import sqlite3
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company, url, match_score FROM jobs ORDER BY id DESC LIMIT 50")
    jobs = []
    for row in cursor.fetchall():
        jobs.append({
            'id': row[0],
            'title': row[1],
            'company': row[2],
            'url': row[3],
            'score': row[4]
        })
    conn.close()
    return jobs

def run_hustlehawk_daemon():
    """Main daemon loop"""
    print("="*80)
    print("🦅 HUSTLEHAWK DAEMON STARTED")
    print(f"Checking every {CHECK_INTERVAL/60} minutes for new jobs...")
    print("="*80)
    
    seen_jobs = load_seen_jobs()
    
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running scrapers...")
            
            # Run all scrapers
            total_found = run_all_scrapers()
            
            # Check for new jobs
            all_jobs = get_new_jobs_from_db()
            new_jobs = [job for job in all_jobs if job['id'] not in seen_jobs]
            
            if new_jobs:
                print(f"\n🎯 Found {len(new_jobs)} NEW jobs!")
                send_discord_notification(new_jobs)
                
                # Mark as seen
                for job in new_jobs:
                    seen_jobs.add(job['id'])
                save_seen_jobs(seen_jobs)
            else:
                print("No new jobs this round.")
            
            print(f"\n💤 Sleeping for {CHECK_INTERVAL/60} minutes...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 HustleHawk daemon stopped!")
            break
        except Exception as e:
            print(f"❌ Error in daemon: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    run_hustlehawk_daemon()
