#!/usr/bin/env python3
"""
HustleHawk Lightweight Scraper - Indeed + RemoteOK
NO SELENIUM - Uses requests only (saves data!)
"""
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
from datetime import datetime
import random

# =============================================================================
# PROFILES
# =============================================================================

PROFILES = {
    'kode': {
        'level': 'junior-mid',
        'keywords': ['python', 'javascript', 'react', 'node', 'nodejs', 'firebase', 'android', 'kotlin'],
        'core_skills': {
            'python': 20, 'javascript': 20, 'react': 18, 'node': 18,
            'firebase': 15, 'android': 15, 'kotlin': 12, 'flutter': 12,
            'api': 10, 'rest': 8, 'git': 8, 'linux': 8, 'docker': 8
        },
        'good_roles': [
            'backend developer', 'full stack', 'python developer',
            'javascript developer', 'web developer', 'software engineer',
            'android developer', 'backend engineer', 'full-stack'
        ],
        'search_terms': [
            'python developer',
            'backend developer',
            'full stack developer',
            'javascript developer'
        ]
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
        ],
        'search_terms': [
            'webflow developer',
            'frontend developer',
            'web designer',
            'no-code developer'
        ]
    }
}

# Instant rejection keywords
REJECT_KEYWORDS = [
    'customer success', 'sales representative', 'account executive',
    'marketing manager', 'finance manager', 'accountant', 'physiotherapist',
    'medical', 'nurse', 'teacher', 'recruiter', 'hr manager', 'hr specialist',
    'data entry', 'virtual assistant', 'customer support', 'sales engineer',
    'account manager', 'business development', 'project manager'
]

ACTIVE_PROFILE = 'kode'
PROFILE = PROFILES[ACTIVE_PROFILE]

# =============================================================================
# DATABASE
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
# STRICT MATCHING ALGORITHM
# =============================================================================

def calculate_match(title, description, profile=None):
    """
    VERY STRICT matching - quality over quantity
    """
    if profile is None:
        profile = PROFILE

    score = 0
    text_lower = f"{title} {description}".lower()
    title_lower = title.lower()

    # === INSTANT REJECTION ===
    for reject_word in REJECT_KEYWORDS:
        if reject_word in title_lower:
            return 0  # Hard reject
    
    # === TITLE MUST MATCH A GOOD ROLE ===
    title_match = False
    for role in profile['good_roles']:
        if role in title_lower:
            title_match = True
            score += 30  # Big boost for title match
            break
    
    if not title_match:
        # No matching role in title? Probably not relevant
        return 0  # Hard reject if title doesn't match

    # === SENIOR/LEAD HARD FILTER (for junior-mid) ===
    if profile['level'] == 'junior-mid':
        senior_keywords = [
            'senior', 'sr.', 'sr ', 'lead ', 'principal', 'staff engineer',
            'director', 'head of', 'chief', 'architect', 'vp ',
            '5+ years', '6+ years', '7+ years', '8+ years', '10+ years'
        ]
        for keyword in senior_keywords:
            if keyword in text_lower:
                return 0  # Hard reject

    # === JUNIOR/ENTRY BOOST ===
    if profile['level'] == 'junior-mid':
        junior_keywords = [
            'junior', 'jr', 'entry level', 'entry-level', 'graduate',
            '0-2 years', '1-3 years', '2-4 years', 'early career', 'associate'
        ]
        for keyword in junior_keywords:
            if keyword in text_lower:
                score += 25
                break

    # === SKILL MATCHING - REQUIRE MINIMUM ===
    skill_matches = 0
    for skill, points in profile['core_skills'].items():
        if skill in text_lower:
            score += points
            skill_matches += 1
    
    # Must have at least 2 skills (strict!)
    if skill_matches < 2:
        return 0  # Hard reject

    # === REMOTE BONUS ===
    if any(loc in text_lower for loc in ['remote', 'work from home', 'worldwide']):
        score += 10

    return max(0, min(score, 100))

# =============================================================================
# INDEED SCRAPER (LIGHTWEIGHT)
# =============================================================================

def scrape_indeed_lightweight(search_term, max_pages=2):
    """
    Scrape Indeed without Selenium - lightweight!
    """
    print(f"\n🔍 Scraping Indeed: '{search_term}'...")
    
    saved_count = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'https://www.indeed.com'
    }
    
    for page in range(max_pages):
        try:
            # Build URL
            query = search_term.replace(' ', '+')
            start = page * 10
            url = f"https://www.indeed.com/jobs?q={query}+remote&l=Remote&start={start}"
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"  ⚠ Indeed returned status {response.status_code}")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            if not job_cards:
                print(f"  ℹ No more jobs found on page {page + 1}")
                break
            
            for card in job_cards:
                try:
                    # Extract title
                    title_elem = card.find('h2', class_='jobTitle')
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    # Extract company
                    company_elem = card.find('span', {'data-testid': 'company-name'})
                    company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
                    
                    # Extract location
                    location_elem = card.find('div', {'data-testid': 'text-location'})
                    location = location_elem.get_text(strip=True) if location_elem else 'Remote'
                    
                    # Extract link
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.indeed.com{job_url}"
                    
                    # Extract description snippet
                    snippet_elem = card.find('div', class_='job-snippet')
                    description = snippet_elem.get_text(strip=True) if snippet_elem else title
                    
                    # Calculate match
                    match_score = calculate_match(title, description)
                    
                    if match_score >= 50:  # Strict threshold
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
                            star = "⭐" if match_score >= 70 else ""
                            print(f"  ✓ {title[:50]} ({match_score}%) {star}")
                
                except Exception as e:
                    continue
            
            # Be nice to Indeed
            time.sleep(random.uniform(2, 4))
        
        except Exception as e:
            print(f"  ✗ Page {page + 1} error: {e}")
            continue
    
    print(f"✓ Indeed: Saved {saved_count} jobs")
    return saved_count

# =============================================================================
# REMOTEOK SCRAPER (IMPROVED)
# =============================================================================

def scrape_remoteok_filtered(search_term):
    """
    RemoteOK with better filtering
    """
    print(f"\n🔍 Scraping RemoteOK: '{search_term}'...")
    
    try:
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ⚠ RemoteOK returned status {response.status_code}")
            return 0
        
        jobs = response.json()[1:]  # Skip metadata
        saved_count = 0
        
        for job in jobs[:30]:  # Check first 30
            try:
                title = job.get('position', 'Unknown')
                company = job.get('company', 'Unknown')
                description = job.get('description', '')
                tags = ', '.join(job.get('tags', []))
                
                # Calculate match
                match_text = f"{title} {description} {tags}"
                match_score = calculate_match(title, match_text)
                
                if match_score >= 50:  # Strict
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
                        star = "⭐" if match_score >= 70 else ""
                        print(f"  ✓ {title[:50]} ({match_score}%) {star}")
            
            except Exception as e:
                continue
        
        print(f"✓ RemoteOK: Saved {saved_count} jobs")
        return saved_count
    
    except Exception as e:
        print(f"✗ RemoteOK error: {e}")
        return 0

# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_lightweight_scrapers(profile_name='kode'):
    """Run lightweight scrapers"""
    global ACTIVE_PROFILE, PROFILE
    ACTIVE_PROFILE = profile_name
    PROFILE = PROFILES[profile_name]
    
    print("="*80)
    print(" "*15 + f"🦅 HUSTLEHAWK LIGHTWEIGHT - {profile_name.upper()}")
    print("="*80)
    print(f"\nLevel: {PROFILE['level']}")
    print(f"Skills: {', '.join(PROFILE['keywords'][:8])}")
    print(f"✅ Low data usage - text only!")
    print(f"✅ Threshold: 50% minimum (strict!)")
    if PROFILE['level'] == 'junior-mid':
        print(f"✅ Auto-rejecting: Senior, Lead, 5+ years")
    print()
    
    total = 0
    
    # Run RemoteOK once (has all types of jobs)
    try:
        count = scrape_remoteok_filtered(PROFILE['keywords'][0])
        total += count
        time.sleep(2)
    except Exception as e:
        print(f"✗ RemoteOK failed: {e}")
    
    # Run Indeed for each search term
    for search_term in PROFILE['search_terms']:
        print(f"\n{'='*80}")
        print(f"🎯 Search: {search_term}")
        print('='*80)
        
        try:
            count = scrape_indeed_lightweight(search_term, max_pages=2)
            total += count
            time.sleep(3)  # Be respectful
        except Exception as e:
            print(f"✗ Indeed '{search_term}' failed: {e}")
    
    print("\n" + "="*80)
    print(f"🦅 FOUND {total} HIGH-QUALITY JOBS (50%+ match, strict filtering)")
    print("="*80)
    return total

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║     🦅 HUSTLEHAWK LIGHTWEIGHT - LOW DATA USAGE 🦅            ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    print("Available profiles:")
    print("  1. kode   - Backend/Full Stack (Python, React, Node)")
    print("  2. leeds  - Webflow Developer (Webflow, Frontend, SEO)")
    print()
    profile = input("Choose profile [kode/leeds] (default: kode): ").strip().lower()
    
    if profile not in ['kode', 'leeds']:
        profile = 'kode'
    
    print("\n💡 This scraper uses minimal data (text only, no browser)")
    print("📊 Strict filtering - only saves 50%+ matches\n")
    
    input("Press Enter to start scraping...")
    
    try:
        total = run_lightweight_scrapers(profile)
        print(f"\n✅ Done! Found {total} quality jobs.")
        print("\n🌐 View in dashboard:")
        print("   python3 dashboard_server.py")
        print("   Then open: http://localhost:8000/dashboard.html")
    except KeyboardInterrupt:
        print("\n\n⛔ Scraping cancelled!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
