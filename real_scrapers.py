#!/usr/bin/env python3
"""
REAL Job Scrapers - Production Ready with Smart Filtering
FIXED VERSION - Proper thresholds and profile selection
"""
from bs4 import BeautifulSoup
import requests
import json
import time
import feedparser
from datetime import datetime
import sqlite3

# =============================================================================
# YOUR PROFILE - UPDATED
# =============================================================================

# === PROFILES ===
PROFILES = {
    'kode': {
        'level': 'entry-level',
        # Expanded keywords for 2025 high-volume trends
        'keywords': [
            'Data entry', 'Virtual assistant', 'Transcription', 'Online tutoring', 
            'Data Annotator', 'Lead Generation', 'Social media assistant', 
            'Email handling', 'Web search evaluator', 'Customer support chat'
        ],
        # Core skills weighted for general administrative and accuracy tasks
        'core_skills': {
            'typing': 25, 'excel': 20, 'google sheets': 20, 'communication': 15,
            'research': 12, 'data validation': 12, 'crm': 10, 'transcription': 10,
            'english': 10, 'attention to detail': 15
        },
        # Modern titles frequently posted on Indeed and Remote boards in 2025
        'good_roles': [
            'Data Entry Clerk', 'Virtual Assistant', 'Admin Intern', 
            'Transcriptionist', 'Data Annotator', 'E-commerce Assistant', 
            'Social Media Manager', 'Customer Service Representative',
            'Lead Generation Specialist', 'Content Moderator'
        ],
        # Optimized search terms for scrapers (2025 specific)
        'search_terms': [
            'Remote Data Entry Hourly',
            'Virtual Assistant No Experience Remote',
            'Remote Data Annotator Entry Level',
            'Online Transcription Jobs Flexible Hours',
            'Remote Customer Support Representative Chat',
            'Administrative Assistant Remote Hourly',
            'Remote Social Media Assistant Worldwide',
            'B2B Lead Generation Remote Hourly'
        ],

    },
    'leeds': {
        'level': 'mid-senior',
        'keywords': ['webflow', 'javascript', 'css', 'html', 'web design', 'frontend', 'seo'],
        'core_skills': {
            'webflow': 25, 'javascript': 20, 'css': 20, 'html': 18,
            'web design': 18, 'frontend': 15, 'figma': 15, 'seo': 12,
            'responsive': 10, 'animation': 10, 'cms': 8
        },
        'good_roles': [
            'webflow developer', 'webflow designer', 'frontend developer',
            'web developer', 'no-code developer', 'webflow expert',
            'web designer'
        ]
    }
}


# Select active profile (will be overridden by user input)
ACTIVE_PROFILE = 'kode'
PROFILE = PROFILES[ACTIVE_PROFILE]

# =============================================================================
# DATABASE HELPER
# =============================================================================

def save_to_db(job, match_score):
    """Save job to database"""
    try:
        conn = sqlite3.connect('jobhunter.db')
        c = conn.cursor()

        c.execute('''INSERT OR REPLACE INTO jobs
                    (job_id, title, company, location, salary, url,
                     description, requirements, posted_date, source, match_score, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (job['id'], job['title'], job['company'],
                  job['location'], job.get('salary', 'Not specified'), job['url'],
                  job.get('description', ''), job.get('requirements', ''),
                  job['posted_date'], job['source'], int(match_score),
                  job.get('tags', '')))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False



# =============================================================================
# SMART MATCHING ALGORITHM
# =============================================================================

def calculate_match(job_text, profile=None):
    """
    Smart matching - filters by level and skills
    Returns score 0-100
    """
    if profile is None:
        profile = PROFILE

    score = 0
    text_lower = job_text.lower()

    # === INSTANT DISQUALIFIERS (if junior/mid level) ===
    if profile['level'] == 'junior-mid':
        senior_keywords = [
            'senior', 'sr.', 'sr ', 'lead', 'principal', 'staff engineer',
            'director', 'manager', 'head of', 'chief', 'architect',
            '5+ years', '7+ years', '10+ years', 'expert level'
        ]
        for keyword in senior_keywords:
            if keyword in text_lower:
                return 5

    # === BIG BOOST for Junior/Entry (if applicable) ===
    if profile['level'] == 'junior-mid':
        junior_keywords = [
            'junior', 'jr', 'entry level', 'entry-level', 'graduate',
            '0-2 years', '1-3 years', 'early career', 'mentorship'
        ]
        for keyword in junior_keywords:
            if keyword in text_lower:
                score += 40
                break

    # === YOUR SKILLS (High value) ===
    skill_count = 0
    for skill, points in profile['core_skills'].items():
        if skill in text_lower:
            score += points
            skill_count += 1

    # === JOB TYPES YOU WANT ===
    for role in profile['good_roles']:
        if role in text_lower:
            score += 15
            break

    # === LOCATION BONUS ===
    if any(loc in text_lower for loc in ['remote', 'worldwide', 'global']):
        score += 10

    return min(score, 100)  # Cap at 100

# =============================================================================
# SCRAPERS
# =============================================================================

def scrape_remotive():
    """Remotive.io - Real remote jobs"""
    print("\n🔍 Scraping Remotive.io...")

    try:
        url = "https://remotive.com/api/remote-jobs"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])

            saved_count = 0

            for job in jobs[:40]:  # Check more jobs
                try:
                    job_data = {
                        'id': f"remotive_{job['id']}",
                        'title': job.get('title', 'Unknown'),
                        'company': job.get('company_name', 'Unknown'),
                        'location': 'Remote',
                        'url': job.get('url', ''),
                        'description': job.get('description', '')[:500],
                        'posted_date': job.get('publication_date', '')[:10],
                        'source': 'Remotive',
                        'tags': job.get('category', '')
                    }

                    match_text = f"{job_data['title']} {job_data['description']} {job_data['tags']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 25 to >= 40 for consistency
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ Remotive: Saved {saved_count} jobs")
            return saved_count

        return 0

    except Exception as e:
        print(f"✗ Remotive error: {e}")
        return 0

def scrape_remoteok_simple():
    """RemoteOK - Simple API approach"""
    print("\n🔍 Scraping RemoteOK (Simple)...")
    try:
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            jobs = response.json()[1:]  # First item is metadata
            saved_count = 0

            for job in jobs[:50]:
                try:
                    job_data = {
                        'id': f"remoteok_{job.get('id')}",
                        'title': job.get('position', 'Unknown'),
                        'company': job.get('company', 'Unknown'),
                        'location': 'Remote',
                        'url': f"https://remoteok.com/remote-jobs/{job.get('id')}",
                        'description': job.get('description', '')[:500],
                        'posted_date': job.get('date', '')[:10] if job.get('date') else datetime.now().strftime('%Y-%m-%d'),
                        'source': 'RemoteOK',
                        'tags': ', '.join(job.get('tags', []))
                    }

                    match_text = f"{job_data['title']} {job_data['description']} {job_data['tags']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ RemoteOK: Saved {saved_count} jobs")
            return saved_count
        return 0
    except Exception as e:
        print(f"✗ RemoteOK error: {e}")
        return 0


def scrape_arbeitnow():
    """Arbeitnow - European remote jobs API"""
    print("\n🔍 Scraping Arbeitnow...")
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            data = response.json()
            jobs = data.get('data', [])
            saved_count = 0

            for job in jobs[:40]:
                try:
                    job_data = {
                        'id': f"arbeitnow_{job.get('slug')}",
                        'title': job.get('title', 'Unknown'),
                        'company': job.get('company_name', 'Unknown'),
                        'location': job.get('location', 'Remote'),
                        'url': job.get('url', ''),
                        'description': job.get('description', '')[:500],
                        'posted_date': job.get('created_at', '')[:10],
                        'source': 'Arbeitnow',
                        'tags': ', '.join(job.get('tags', []))
                    }

                    match_text = f"{job_data['title']} {job_data['description']} {job_data['tags']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ Arbeitnow: Saved {saved_count} jobs")
            return saved_count
        return 0
    except Exception as e:
        print(f"✗ Arbeitnow error: {e}")
        return 0

def scrape_github_jobs_rss():
    """RSS feeds from multiple sources"""
    print("\n🔍 Scraping RSS Feeds...")

    try:
        rss_feeds = [
            'https://remoteok.com/remote-dev-jobs.rss',
            'https://www.remoteonly.org/rss',
        ]

        saved_count = 0

        for rss_url in rss_feeds:
            try:
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:20]:
                    try:
                        job_data = {
                            'id': f"rss_{hash(entry.link)}",
                            'title': entry.get('title', 'Unknown'),
                            'company': entry.get('author', 'Unknown'),
                            'location': 'Remote',
                            'url': entry.get('link', ''),
                            'description': entry.get('summary', '')[:500],
                            'posted_date': entry.get('published', datetime.now().strftime('%Y-%m-%d'))[:10],
                            'source': 'RSS Feed',
                            'tags': ', '.join([tag.term for tag in entry.get('tags', [])][:3])
                        }

                        match_text = f"{job_data['title']} {job_data['description']}"
                        match_score = calculate_match(match_text)

                        # FIXED: Changed from >= 15 to >= 40
                        if match_score >= 40:
                            if save_to_db(job_data, match_score):
                                saved_count += 1
                                level = "⭐" if match_score >= 70 else ""
                                print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                    except Exception as e:
                        continue

            except Exception as e:
                continue

        print(f"✓ RSS Feeds: Saved {saved_count} jobs")
        return saved_count

    except Exception as e:
        print(f"✗ RSS error: {e}")
        return 0

def scrape_weworkremotely():
    """We Work Remotely - High quality remote jobs"""
    print("\n🔍 Scraping WeWorkRemotely...")
    try:
        url = "https://weworkremotely.com/categories/remote-programming-jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Updated selectors for their actual HTML structure
            jobs = soup.find_all('li')
            saved_count = 0

            for job in jobs[:40]:
                try:
                    link = job.find('a', href=True)
                    if not link or '/remote-jobs/' not in link.get('href', ''):
                        continue

                    title_elem = link.find('span', class_='title')
                    company_elem = link.find('span', class_='company')

                    if not title_elem:
                        continue

                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else 'Unknown'
                    job_url = f"https://weworkremotely.com{link['href']}"

                    job_data = {
                        'id': f"wwr_{link['href'].split('/')[-1]}",
                        'title': title,
                        'company': company,
                        'location': 'Remote',
                        'url': job_url,
                        'description': title,
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'WeWorkRemotely',
                        'tags': 'Programming'
                    }

                    match_text = f"{job_data['title']} {job_data['description']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ WeWorkRemotely: Saved {saved_count} jobs")
            return saved_count
        return 0
    except Exception as e:
        print(f"✗ WeWorkRemotely error: {e}")
        return 0


def scrape_himalayas():
    """Himalayas - with better headers to avoid 403"""
    print("\n🔍 Scraping Himalayas...")
    try:
        url = "https://himalayas.app/jobs/software-developer"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://himalayas.app/'
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Try different selectors
            jobs = soup.find_all('div', class_='job') or soup.find_all('a', href=lambda x: x and '/jobs/' in x)
            saved_count = 0

            for job in jobs[:30]:
                try:
                    if job.name == 'a':
                        title = job.text.strip()
                        job_url = job['href']
                    else:
                        title_elem = job.find(['h2', 'h3', 'a'])
                        if not title_elem:
                            continue
                        title = title_elem.text.strip()
                        link = job.find('a', href=True)
                        job_url = link['href'] if link else ''

                    if not title or len(title) < 5:
                        continue

                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://himalayas.app{job_url}"

                    job_data = {
                        'id': f"himalayas_{hash(title)}",
                        'title': title,
                        'company': 'Various',
                        'location': 'Remote',
                        'url': job_url or 'https://himalayas.app/jobs',
                        'description': title,
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'Himalayas',
                        'tags': 'Remote'
                    }

                    match_text = f"{job_data['title']} {job_data['description']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ Himalayas: Saved {saved_count} jobs")
            return saved_count
        else:
            print(f"✗ Himalayas returned status {response.status_code}")
        return 0
    except Exception as e:
        print(f"✗ Himalayas error: {e}")
        return 0


def scrape_turing():
    """Turing - Remote developer jobs"""
    print("\n🔍 Scraping Turing...")
    try:
        url = "https://www.turing.com/jobs"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = soup.find_all('div', class_='job-card', limit=30)
            saved_count = 0

            for job in jobs:
                try:
                    title_elem = job.find('h3') or job.find('h2') or job.find('a')
                    if not title_elem:
                        continue

                    title = title_elem.text.strip()

                    job_data = {
                        'id': f"turing_{hash(title)}",
                        'title': title,
                        'company': 'Various (Turing)',
                        'location': 'Remote',
                        'url': 'https://www.turing.com/jobs',
                        'description': title,
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'Turing',
                        'tags': 'Remote'
                    }

                    match_text = f"{job_data['title']} {job_data['description']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ Turing: Saved {saved_count} jobs")
            return saved_count
        return 0
    except Exception as e:
        print(f"✗ Turing error: {e}")
        return 0

def scrape_wellfound():
    """Wellfound (AngelList) - Startup jobs"""
    print("\n🔍 Scraping Wellfound...")
    try:
        # Note: AngelList requires auth for full API, but we can scrape their public pages
        url = "https://wellfound.com/role/r/software-engineer"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # This is a simplified version - AngelList structure changes often
            jobs = soup.find_all('div', class_='job-listing')[:30]
            saved_count = 0

            for job in jobs:
                try:
                    # Parse job data (adjust selectors as needed)
                    title = job.find('h2') or job.find('a')
                    if not title:
                        continue

                    job_data = {
                        'id': f"wellfound_{hash(title.text)}",
                        'title': title.text.strip(),
                        'company': 'Startup',
                        'location': 'Remote',
                        'url': 'https://wellfound.com',
                        'description': title.text.strip(),
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'Wellfound',
                        'tags': 'Startup'
                    }

                    match_text = f"{job_data['title']} {job_data['description']}"
                    match_score = calculate_match(match_text)

                    # FIXED: Changed from >= 0 to >= 40
                    if match_score >= 40:
                        if save_to_db(job_data, match_score):
                            saved_count += 1
                            level = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {job_data['title'][:50]} ({match_score}%) {level}")

                except Exception as e:
                    continue

            print(f"✓ Wellfound: Saved {saved_count} jobs")
            return saved_count
        return 0
    except Exception as e:
        print(f"✗ Wellfound error: {e}")
        return 0

# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_all_scrapers(profile_name='kode'):
    """Run all scrapers for a specific profile"""
    global ACTIVE_PROFILE, PROFILE
    ACTIVE_PROFILE = profile_name
    PROFILE = PROFILES[profile_name]

    print("="*80)
    print(" "*20 + f"🦅 HUSTLEHAWK - JOB HUNTING ({profile_name.upper()})")
    print("="*80)
    print(f"\nYour Level: {PROFILE['level']}")
    print(f"Skills: {', '.join(PROFILE['keywords'][:8])}")
    if PROFILE['level'] == 'junior-mid':
        print(f"Filtering OUT: Senior, Lead, 5+ years exp")
    print()

    total = 0
    scrapers = [
        ('Remotive', scrape_remotive),
        ('RemoteOK', scrape_remoteok_simple),
        ('Arbeitnow', scrape_arbeitnow),
        ('RSS Feeds', scrape_github_jobs_rss),
    ]

    for name, scraper_func in scrapers:
        try:
            count = scraper_func()
            total += count
            time.sleep(3)
        except Exception as e:
            print(f"✗ {name} failed: {e}")
            continue

    print("\n" + "="*80)
    print(f"🦅 HUSTLEHAWK FOUND {total} QUALITY MATCHES (40%+ score)")
    print("="*80)
    return total

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║           🦅 HUSTLEHAWK - SMART JOB SCRAPER 🦅               ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    # Choose which profile to run for
    print("Available profiles:")
    print("  1. kode   - Backend/Full Stack (Python, React, Node)")
    print("  2. leeds  - Webflow Developer (Webflow, Frontend, SEO)")
    print()
    profile = input("Choose profile [kode/leeds] (default: kode): ").strip().lower()

    # Default to 'kode' if nothing entered
    if profile not in ['kode', 'leeds']:
        profile = 'kode'

    # FIXED: Removed premature print statement - it's now inside run_all_scrapers()
    input("\nPress Enter to start scraping...")

    try:
        total = run_all_scrapers(profile)
        print(f"\n✓ Done! Found {total} jobs matching {profile.upper()}'s level.")
        print("\n🌐 View in dashboard:")
        print("   python3 dashboard_server.py")
        print("   Then open: http://localhost:8000/dashboard.html")
    except KeyboardInterrupt:
        print("\n\nScraping cancelled!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
