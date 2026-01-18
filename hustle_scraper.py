#!/usr/bin/env python3
"""
HustleHawk - Easy Remote Gigs Scraper
Jobs for everyone - devs, non-devs, friends, family!
UPDATED: With date tracking and auto-cleanup
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
from datetime import datetime, timedelta
import random

# =============================================================================
# PROFILES - DEV + NON-DEV GIGS
# =============================================================================

PROFILES = {
    # === DEVELOPER PROFILES ===
    'kode': {
        'level': 'junior-mid',
        'category': 'Developer',
        'keywords': ['python', 'javascript', 'react', 'node', 'backend', 'full stack'],
        'core_skills': {
            'python': 20, 'javascript': 20, 'react': 18, 'node': 18,
            'firebase': 15, 'android': 15, 'kotlin': 12, 'flutter': 12,
            'api': 10, 'rest': 8, 'git': 8, 'linux': 8, 'docker': 8
        },
        'good_roles': [
            'backend developer', 'full stack', 'python developer',
            'javascript developer', 'web developer', 'software engineer',
            'android developer', 'backend engineer'
        ],
        'search_terms': [
            'Python Developer Remote',
            'Backend Developer Remote',
            'Full Stack Developer Remote'
        ],
        'reject_senior': True
    },
    
    'leeds': {
        'level': 'mid-senior',
        'category': 'Developer',
        'keywords': ['webflow', 'frontend', 'web design', 'figma', 'seo'],
        'core_skills': {
            'webflow': 25, 'javascript': 20, 'css': 20, 'html': 18,
            'web design': 18, 'frontend': 15, 'figma': 15, 'seo': 12,
            'responsive': 10, 'animation': 10, 'cms': 8
        },
        'good_roles': [
            'webflow developer', 'webflow designer', 'frontend developer',
            'web developer', 'no-code developer', 'web designer'
        ],
        'search_terms': [
            'Webflow Developer Remote',
            'Frontend Developer Remote',
            'Web Designer Remote'
        ],
        'reject_senior': False
    },
    
    # === EASY REMOTE GIGS ===
    'hustler': {
        'level': 'entry',
        'category': 'Easy Remote Gigs',
        'keywords': ['virtual assistant', 'data entry', 'customer support', 'remote', 'hourly'],
        'core_skills': {
            'virtual assistant': 25, 'data entry': 25, 'customer support': 20,
            'customer service': 20, 'email': 15, 'chat support': 15,
            'administrative': 15, 'scheduling': 10, 'organization': 10
        },
        'good_roles': [
            'virtual assistant', 'data entry', 'customer support',
            'customer service', 'administrative assistant', 'chat support',
            'email support', 'remote assistant', 'online assistant'
        ],
        'search_terms': [
            'Virtual Assistant Remote',
            'Data Entry Remote',
            'Customer Support Remote',
            'Remote Assistant'
        ],
        'reject_senior': False,
        'hourly_rate': '$10-25/hour'
    },
    
    'freelancer': {
        'level': 'entry-mid',
        'category': 'Freelance/Creative',
        'keywords': ['writing', 'content', 'social media', 'copywriting', 'graphic design'],
        'core_skills': {
            'content writing': 25, 'copywriting': 25, 'social media': 20,
            'writing': 20, 'blog': 15, 'seo': 15, 'editing': 12,
            'graphic design': 12, 'canva': 10, 'video editing': 10
        },
        'good_roles': [
            'content writer', 'copywriter', 'social media manager',
            'writer', 'blogger', 'content creator', 'freelance writer',
            'social media coordinator', 'community manager'
        ],
        'search_terms': [
            'Content Writer Remote',
            'Social Media Manager Remote',
            'Copywriter Remote',
            'Freelance Writer Remote'
        ],
        'reject_senior': False,
        'hourly_rate': '$15-35/hour'
    },
    
    'sidehustle': {
        'level': 'entry',
        'category': 'Side Hustle',
        'keywords': ['part time', 'tutor', 'teaching', 'online tutor', 'flexible'],
        'core_skills': {
            'teaching': 25, 'tutoring': 25, 'english': 20, 'education': 20,
            'online teaching': 18, 'esl': 15, 'training': 12,
            'mentoring': 10, 'coaching': 10
        },
        'good_roles': [
            'tutor', 'online tutor', 'english teacher', 'esl teacher',
            'teaching assistant', 'online instructor', 'educator',
            'language tutor', 'mentor'
        ],
        'search_terms': [
            'Online Tutor Remote',
            'ESL Teacher Remote',
            'Part Time Tutor Remote',
            'Online Teaching Remote'
        ],
        'reject_senior': False,
        'hourly_rate': '$12-30/hour'
    }
}

# Global reject keywords (still filter out completely unrelated stuff)
GLOBAL_REJECT = [
    'physiotherapist', 'medical doctor', 'nurse practitioner',
    'surgeon', 'pharmacist', 'lawyer', 'attorney'
]

ACTIVE_PROFILE = 'kode'
PROFILE = PROFILES[ACTIVE_PROFILE]

# =============================================================================
# DATABASE CLEANUP
# =============================================================================

def cleanup_old_jobs():
    """Delete jobs older than 7 days"""
    try:
        conn = sqlite3.connect('jobhunter.db')
        c = conn.cursor()
        
        # Calculate date 7 days ago
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Count jobs to be deleted
        c.execute("SELECT COUNT(*) FROM jobs WHERE scrape_date < ?", (seven_days_ago,))
        count = c.fetchone()[0]
        
        if count > 0:
            print(f"\n🗑️  Cleaning up {count} jobs older than 7 days...")
            c.execute("DELETE FROM jobs WHERE scrape_date < ?", (seven_days_ago,))
            conn.commit()
            print(f"✓ Cleanup complete!\n")
        
        conn.close()
    except Exception as e:
        print(f"⚠ Cleanup warning: {e} (scrape_date column may not exist yet)\n")

# =============================================================================
# DATABASE
# =============================================================================

def save_to_db(job, match_score):
    """Save job to database with scrape date"""
    try:
        conn = sqlite3.connect('jobhunter.db')
        c = conn.cursor()
        
        # Add scrape_date to track when job was found
        today = datetime.now().strftime('%Y-%m-%d')
        
        c.execute('''INSERT OR REPLACE INTO jobs
                    (job_id, title, company, location, salary, url,
                     description, requirements, posted_date, source, match_score, tags, scrape_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (job['id'], job['title'], job['company'],
                  job['location'], job.get('salary', 'Not specified'), job['url'],
                  job.get('description', ''), job.get('requirements', ''),
                  job['posted_date'], job['source'], int(match_score),
                  job.get('tags', ''), today))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"    ⚠ DB Error: {e}")
        return False

# =============================================================================
# SMART MATCHING - WORKS FOR DEV + NON-DEV
# =============================================================================

def calculate_match(title, description, profile=None):
    """
    Smart matching for ANY job type
    """
    if profile is None:
        profile = PROFILE

    score = 0
    text_lower = f"{title} {description}".lower()
    title_lower = title.lower()

    # === GLOBAL REJECTION (medical/legal only) ===
    for reject_word in GLOBAL_REJECT:
        if reject_word in title_lower:
            return 0
    
    # === TITLE MATCHING ===
    title_match = False
    for role in profile['good_roles']:
        if role in title_lower:
            title_match = True
            score += 30
            break
    
    # Generic matches (less specific but still good)
    if 'remote' in title_lower:
        score += 5
    if 'assistant' in title_lower and profile['category'] == 'Easy Remote Gigs':
        score += 15
    if 'support' in title_lower and profile['category'] == 'Easy Remote Gigs':
        score += 15

    # === SENIOR FILTER (only for dev profiles requesting it) ===
    if profile.get('reject_senior', False):
        senior_keywords = [
            'senior', 'sr.', 'sr ', 'lead ', 'principal', 'staff engineer',
            'director', 'head of', 'chief', 'architect',
            '5+ years', '7+ years', '10+ years'
        ]
        for keyword in senior_keywords:
            if keyword in text_lower:
                return 0

    # === JUNIOR/ENTRY BOOST ===
    if profile['level'] in ['junior-mid', 'entry']:
        entry_keywords = [
            'junior', 'entry level', 'entry-level', 'beginner',
            'no experience', '0-2 years', '1-3 years', 'trainee'
        ]
        for keyword in entry_keywords:
            if keyword in text_lower:
                score += 25
                break

    # === SKILL MATCHING ===
    skill_matches = 0
    for skill, points in profile['core_skills'].items():
        if skill in text_lower:
            score += points
            skill_matches += 1
    
    # Require at least 1 skill match
    if skill_matches < 1:
        score -= 10

    # === HOURLY RATE BONUS (for gig profiles) ===
    if 'hourly' in text_lower or '/hour' in text_lower or '$' in text_lower:
        if profile['category'] in ['Easy Remote Gigs', 'Side Hustle', 'Freelance/Creative']:
            score += 10

    return max(0, min(score, 100))

# =============================================================================
# SELENIUM DRIVER SETUP
# =============================================================================

def setup_driver(headless=True):
    """Setup Chromium driver"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless=new')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
    
    try:
        print(f"  🔍 Starting Chromium...")
        chrome_options.binary_location = '/snap/bin/chromium'
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"  ⚠ Error: {str(e)[:80]}")
        raise

def human_delay():
    """Random delay"""
    time.sleep(random.uniform(2, 4))

# =============================================================================
# INDEED SCRAPER
# =============================================================================

def scrape_indeed(search_term, max_jobs=30):
    """Scrape Indeed"""
    print(f"\n🔍 Scraping Indeed: '{search_term}'...")
    
    driver = setup_driver(headless=True)
    saved_count = 0
    
    try:
        search_query = search_term.replace(' ', '+')
        url = f"https://www.indeed.com/jobs?q={search_query}&l=Remote&sc=0kf%3Aattr%28DSQF7%29%3B"
        
        driver.get(url)
        human_delay()
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mosaic-provider-jobcards"))
            )
        except:
            print("  ⚠ Could not load Indeed jobs")
            return 0
        
        job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
        
        for card in job_cards[:max_jobs]:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span")
                title = title_elem.text.strip()
                
                company_elem = card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']")
                company = company_elem.text.strip()
                
                location_elem = card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']")
                location = location_elem.text.strip()
                
                link_elem = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                job_url = link_elem.get_attribute('href')
                if not job_url.startswith('http'):
                    job_url = f"https://www.indeed.com{job_url}"
                
                try:
                    snippet_elem = card.find_element(By.CLASS_NAME, "job-snippet")
                    description = snippet_elem.text.strip()
                except:
                    description = title
                
                match_score = calculate_match(title, description)
                
                if match_score >= 35:  # Lower threshold for easy gigs
                    job_data = {
                        'id': f"indeed_{hash(job_url)}",
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': job_url,
                        'description': description[:500],
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'Indeed',
                        'tags': search_term
                    }
                    
                    if save_to_db(job_data, match_score):
                        saved_count += 1
                        star = "⭐" if match_score >= 60 else ""
                        print(f"  ✓ {title[:50]} ({match_score}%) {star}")
            
            except Exception as e:
                continue
        
        print(f"✓ Indeed: Saved {saved_count} jobs")
        return saved_count
        
    except Exception as e:
        print(f"✗ Indeed error: {e}")
        return 0
    finally:
        driver.quit()

# =============================================================================
# REMOTEOK SCRAPER (API - NO SELENIUM)
# =============================================================================

def scrape_remoteok():
    """Scrape RemoteOK API"""
    print(f"\n🔍 Scraping RemoteOK...")
    
    try:
        url = "https://remoteok.com/api"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ⚠ RemoteOK returned {response.status_code}")
            return 0
        
        jobs = response.json()[1:]  # Skip metadata
        saved_count = 0
        
        for job in jobs[:50]:
            try:
                title = job.get('position', 'Unknown')
                company = job.get('company', 'Unknown')
                description = job.get('description', '')
                tags = ', '.join(job.get('tags', []))
                
                match_text = f"{title} {description} {tags}"
                match_score = calculate_match(title, match_text)
                
                if match_score >= 35:
                    job_data = {
                        'id': f"remoteok_{job.get('id')}",
                        'title': title,
                        'company': company,
                        'location': 'Remote',
                        'url': f"https://remoteok.com/remote-jobs/{job.get('id')}",
                        'description': description[:500],
                        'posted_date': job.get('date', '')[:10] if job.get('date') else datetime.now().strftime('%Y-%m-%d'),
                        'source': 'RemoteOK',
                        'tags': tags
                    }
                    
                    if save_to_db(job_data, match_score):
                        saved_count += 1
                        star = "⭐" if match_score >= 60 else ""
                        print(f"  ✓ {title[:50]} ({match_score}%) {star}")
            
            except Exception as e:
                continue
        
        print(f"✓ RemoteOK: Saved {saved_count} jobs")
        return saved_count
    
    except Exception as e:
        print(f"✗ RemoteOK error: {e}")
        return 0

# =============================================================================
# FLEXJOBS SCRAPER (SELENIUM)
# =============================================================================

def scrape_flexjobs(search_term):
    """
    Scrape FlexJobs (basic scraping - they have a paywall)
    """
    print(f"\n🔍 Scraping FlexJobs: '{search_term}'...")
    
    driver = setup_driver(headless=True)
    saved_count = 0
    
    try:
        search_query = search_term.replace(' ', '-').lower()
        url = f"https://www.flexjobs.com/search?search={search_query}&location=Remote"
        
        driver.get(url)
        human_delay()
        
        # FlexJobs structure varies - basic extraction
        job_listings = driver.find_elements(By.CSS_SELECTOR, "li.job, div.job-listing, article")
        
        for listing in job_listings[:20]:
            try:
                title = listing.find_element(By.CSS_SELECTOR, "h2, h3, .job-title, a").text.strip()
                
                if not title or len(title) < 5:
                    continue
                
                try:
                    company = listing.find_element(By.CSS_SELECTOR, ".company, .employer").text.strip()
                except:
                    company = "Various"
                
                try:
                    link = listing.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
                except:
                    link = url
                
                match_score = calculate_match(title, title)
                
                if match_score >= 35:
                    job_data = {
                        'id': f"flexjobs_{hash(link)}",
                        'title': title,
                        'company': company,
                        'location': 'Remote',
                        'url': link,
                        'description': title,
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'FlexJobs',
                        'tags': search_term
                    }
                    
                    if save_to_db(job_data, match_score):
                        saved_count += 1
                        star = "⭐" if match_score >= 60 else ""
                        print(f"  ✓ {title[:50]} ({match_score}%) {star}")
            
            except Exception as e:
                continue
        
        print(f"✓ FlexJobs: Saved {saved_count} jobs")
        return saved_count
        
    except Exception as e:
        print(f"✗ FlexJobs error: {e}")
        return 0
    finally:
        driver.quit()

# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_hustle_scrapers(profile_name='kode'):
    """Run scrapers for any profile"""
    global ACTIVE_PROFILE, PROFILE
    ACTIVE_PROFILE = profile_name
    PROFILE = PROFILES[profile_name]
    
    # Clean up old jobs (older than 7 days)
    cleanup_old_jobs()
    
    print("="*80)
    print(" "*15 + f"🦅 HUSTLEHAWK - {PROFILE['category'].upper()}")
    print("="*80)
    print(f"\nProfile: {profile_name.upper()}")
    print(f"Level: {PROFILE['level']}")
    print(f"Skills: {', '.join(list(PROFILE['keywords'])[:5])}")
    if 'hourly_rate' in PROFILE:
        print(f"💰 Target Rate: {PROFILE['hourly_rate']}")
    print(f"Threshold: 35% minimum")
    print()
    
    total = 0
    
    # RemoteOK (fast API call)
    try:
        count = scrape_remoteok()
        total += count
        time.sleep(2)
    except Exception as e:
        print(f"✗ RemoteOK failed: {e}")
    
    # Indeed searches
    for search_term in PROFILE['search_terms']:
        print(f"\n{'='*80}")
        print(f"🎯 Search: {search_term}")
        print('='*80)
        
        try:
            count = scrape_indeed(search_term, max_jobs=20)
            total += count
            human_delay()
        except Exception as e:
            print(f"✗ Indeed failed: {e}")
    
    # FlexJobs (first search term only)
    try:
        count = scrape_flexjobs(PROFILE['search_terms'][0])
        total += count
    except Exception as e:
        print(f"✗ FlexJobs failed: {e}")
    
    print("\n" + "="*80)
    print(f"🦅 FOUND {total} JOBS FOR {profile_name.upper()}")
    print(f"📅 Jobs saved with today's date for dashboard filtering")
    print("="*80)
    return total

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║        🦅 HUSTLEHAWK - JOBS FOR EVERYONE 🦅                  ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    print("Available profiles:")
    print("  DEV JOBS:")
    print("    1. kode        - Backend/Full Stack (Python, React, Node)")
    print("    2. leeds       - Webflow Developer (Webflow, Frontend)")
    print()
    print("  EASY REMOTE GIGS:")
    print("    3. hustler     - VA, Data Entry, Support ($10-25/hr)")
    print("    4. freelancer  - Writing, Social Media ($15-35/hr)")
    print("    5. sidehustle  - Tutoring, Teaching ($12-30/hr)")
    print()
    
    profile = input("Choose profile [1-5] (default: hustler): ").strip()
    
    profile_map = {
        '1': 'kode',
        '2': 'leeds',
        '3': 'hustler',
        '4': 'freelancer',
        '5': 'sidehustle',
        'kode': 'kode',
        'leeds': 'leeds',
        'hustler': 'hustler',
        'freelancer': 'freelancer',
        'sidehustle': 'sidehustle'
    }
    
    profile = profile_map.get(profile, 'hustler')
    
    print(f"\n💡 Scraping {PROFILES[profile]['category']} jobs...")
    print("📊 Sources: Indeed, RemoteOK, FlexJobs")
    print("📅 Tracking scrape dates for dashboard filtering\n")
    
    input("Press Enter to start scraping...")
    
    try:
        total = run_hustle_scrapers(profile)
        print(f"\n✅ Done! Found {total} jobs for {profile.upper()}.")
        print("\n🌐 View in dashboard:")
        print("   python3 dashboard_server.py")
        print("   Then open: http://localhost:8000/dashboard.html")
        print("\n💡 Share these jobs with friends and family!")
    except KeyboardInterrupt:
        print("\n\n⛔ Scraping cancelled!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
