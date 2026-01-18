#!/usr/bin/env python3
"""
HustleHawk Selenium Scraper - LinkedIn & Indeed
High-quality job scraping with strict filtering
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
            'android developer'
        ],
        'search_terms': [
            'Python Developer Remote',
            'Backend Developer Remote',
            'Full Stack Developer Remote',
            'JavaScript Developer Remote'
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
            'Webflow Developer Remote',
            'Frontend Developer Remote',
            'Web Designer Remote',
            'No-code Developer Remote'
        ]
    }
}

# Instant rejection keywords
REJECT_KEYWORDS = [
    'customer success', 'sales representative', 'account executive',
    'marketing manager', 'finance', 'accountant', 'physiotherapist',
    'medical', 'nurse', 'teacher', 'recruiter', 'hr manager',
    'data entry', 'virtual assistant', 'customer support'
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
        print(f"    ⚠ DB Error: {e}")
        return False

# =============================================================================
# IMPROVED MATCHING ALGORITHM
# =============================================================================

def calculate_match(title, description, profile=None):
    """
    STRICT matching algorithm
    Returns score 0-100
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
    
    # === TITLE MUST BE RELEVANT ===
    title_has_role = False
    for role in profile['good_roles']:
        if role in title_lower:
            title_has_role = True
            score += 25  # Big boost for title match
            break
    
    if not title_has_role:
        # If title doesn't match ANY good role, be very skeptical
        score -= 20

    # === SENIOR/LEAD FILTER (for junior-mid) ===
    if profile['level'] == 'junior-mid':
        senior_keywords = [
            'senior', 'sr.', 'sr ', 'lead', 'principal', 'staff engineer',
            'director', 'manager', 'head of', 'chief', 'architect',
            '5+ years', '7+ years', '10+ years', 'expert level', '8+ years'
        ]
        for keyword in senior_keywords:
            if keyword in text_lower:
                return 0  # Hard reject for junior-mid

    # === JUNIOR BOOST ===
    if profile['level'] == 'junior-mid':
        junior_keywords = [
            'junior', 'jr', 'entry level', 'entry-level', 'graduate',
            '0-2 years', '1-3 years', '2-4 years', 'early career'
        ]
        for keyword in junior_keywords:
            if keyword in text_lower:
                score += 30
                break

    # === SKILL MATCHING (require at least 3 skills) ===
    skill_matches = 0
    for skill, points in profile['core_skills'].items():
        if skill in text_lower:
            score += points
            skill_matches += 1
    
    # Require minimum skill matches
    if skill_matches < 3:
        score -= 15  # Penalty for too few skills

    # === REMOTE BONUS ===
    if any(loc in text_lower for loc in ['remote', 'worldwide', 'work from home']):
        score += 8

    return max(0, min(score, 100))  # Clamp between 0-100

# =============================================================================
# SELENIUM SETUP
# =============================================================================

def setup_driver(headless=True):
    """Setup Chrome/Chromium driver with options"""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')  # For Linux stability
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Try to find Chromium binary (for Linux)
    chrome_options.binary_location = '/usr/bin/chromium-browser'
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        # Fallback: try without specifying binary location
        print(f"  ⚠ Trying alternative Chrome path...")
        chrome_options.binary_location = '/usr/bin/chromium'
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

def human_delay():
    """Random human-like delay"""
    time.sleep(random.uniform(2, 4))

# =============================================================================
# LINKEDIN SCRAPER
# =============================================================================

def scrape_linkedin(search_term, max_jobs=20):
    """
    Scrape LinkedIn jobs
    NOTE: LinkedIn requires login for full access, this is basic scraping
    """
    print(f"\n🔍 Scraping LinkedIn: '{search_term}'...")
    
    driver = setup_driver(headless=False)  # Show browser for LinkedIn
    saved_count = 0
    
    try:
        # Build search URL
        search_query = search_term.replace(' ', '%20')
        url = f"https://www.linkedin.com/jobs/search?keywords={search_query}&location=Worldwide&f_WT=2"
        
        driver.get(url)
        human_delay()
        
        # Wait for jobs to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
            )
        except:
            print("  ⚠ Could not load LinkedIn jobs (may require login)")
            return 0
        
        # Scroll to load more jobs
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
        
        # Find job cards
        job_cards = driver.find_elements(By.CLASS_NAME, "job-search-card")
        
        for idx, card in enumerate(job_cards[:max_jobs]):
            try:
                # Extract job info
                title_elem = card.find_element(By.CLASS_NAME, "base-search-card__title")
                title = title_elem.text.strip()
                
                company_elem = card.find_element(By.CLASS_NAME, "base-search-card__subtitle")
                company = company_elem.text.strip()
                
                location_elem = card.find_element(By.CLASS_NAME, "job-search-card__location")
                location = location_elem.text.strip()
                
                link_elem = card.find_element(By.CSS_SELECTOR, "a.base-card__full-link")
                job_url = link_elem.get_attribute('href')
                
                # Click to get description (optional, slows down scraping)
                description = title  # Use title as fallback
                
                # Calculate match
                match_score = calculate_match(title, description)
                
                if match_score >= 50:  # Strict threshold
                    job_data = {
                        'id': f"linkedin_{hash(job_url)}",
                        'title': title,
                        'company': company,
                        'location': location,
                        'url': job_url,
                        'description': description[:500],
                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                        'source': 'LinkedIn',
                        'tags': search_term
                    }
                    
                    if save_to_db(job_data, match_score):
                        saved_count += 1
                        star = "⭐" if match_score >= 70 else ""
                        print(f"  ✓ {title[:50]} ({match_score}%) {star}")
                
            except Exception as e:
                continue
        
        print(f"✓ LinkedIn: Saved {saved_count} jobs")
        return saved_count
        
    except Exception as e:
        print(f"✗ LinkedIn error: {e}")
        return 0
    finally:
        driver.quit()

# =============================================================================
# INDEED SCRAPER
# =============================================================================

def scrape_indeed(search_term, max_jobs=30):
    """
    Scrape Indeed jobs - more scraper-friendly than LinkedIn
    """
    print(f"\n🔍 Scraping Indeed: '{search_term}'...")
    
    driver = setup_driver(headless=True)
    saved_count = 0
    
    try:
        # Build search URL
        search_query = search_term.replace(' ', '+')
        url = f"https://www.indeed.com/jobs?q={search_query}&l=Remote&sc=0kf%3Aattr%28DSQF7%29%3B"
        
        driver.get(url)
        human_delay()
        
        # Wait for results
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mosaic-provider-jobcards"))
            )
        except:
            print("  ⚠ Could not load Indeed jobs")
            return 0
        
        # Find job cards
        job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
        
        for card in job_cards[:max_jobs]:
            try:
                # Extract info
                title_elem = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span")
                title = title_elem.text.strip()
                
                company_elem = card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']")
                company = company_elem.text.strip()
                
                location_elem = card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']")
                location = location_elem.text.strip()
                
                # Get job link
                link_elem = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                job_url = link_elem.get_attribute('href')
                if not job_url.startswith('http'):
                    job_url = f"https://www.indeed.com{job_url}"
                
                # Try to get snippet
                try:
                    snippet_elem = card.find_element(By.CLASS_NAME, "job-snippet")
                    description = snippet_elem.text.strip()
                except:
                    description = title
                
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
        
        print(f"✓ Indeed: Saved {saved_count} jobs")
        return saved_count
        
    except Exception as e:
        print(f"✗ Indeed error: {e}")
        return 0
    finally:
        driver.quit()

# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_selenium_scrapers(profile_name='kode'):
    """Run Selenium scrapers for LinkedIn and Indeed"""
    global ACTIVE_PROFILE, PROFILE
    ACTIVE_PROFILE = profile_name
    PROFILE = PROFILES[profile_name]
    
    print("="*80)
    print(" "*20 + f"🦅 HUSTLEHAWK SELENIUM - {profile_name.upper()}")
    print("="*80)
    print(f"\nLevel: {PROFILE['level']}")
    print(f"Skills: {', '.join(PROFILE['keywords'][:8])}")
    print(f"Threshold: 50% minimum match (strict!)")
    if PROFILE['level'] == 'junior-mid':
        print(f"Auto-rejecting: Senior, Lead, 5+ years")
    print()
    
    total = 0
    
    # Run searches for each search term
    for search_term in PROFILE['search_terms']:
        print(f"\n{'='*80}")
        print(f"🎯 Search: {search_term}")
        print('='*80)
        
        # Scrape Indeed (more reliable)
        try:
            count = scrape_indeed(search_term, max_jobs=20)
            total += count
            human_delay()
        except Exception as e:
            print(f"✗ Indeed failed: {e}")
        
        # Scrape LinkedIn (may need login)
        try:
            count = scrape_linkedin(search_term, max_jobs=15)
            total += count
            human_delay()
        except Exception as e:
            print(f"✗ LinkedIn failed: {e}")
    
    print("\n" + "="*80)
    print(f"🦅 FOUND {total} HIGH-QUALITY JOBS (50%+ match)")
    print("="*80)
    return total

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║        🦅 HUSTLEHAWK SELENIUM - LINKEDIN & INDEED 🦅         ║")
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
    
    print("\n⚙️  Installing ChromeDriver if needed...")
    print("📢 Note: LinkedIn may require login. Indeed works without login.\n")
    
    input("Press Enter to start scraping...")
    
    try:
        total = run_selenium_scrapers(profile)
        print(f"\n✅ Done! Found {total} quality jobs.")
        print("\n🌐 View in dashboard:")
        print("   python3 dashboard_server.py")
        print("   Then open: http://localhost:8000/dashboard.html")
    except KeyboardInterrupt:
        print("\n\n⛔ Scraping cancelled!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Install: pip install selenium webdriver-manager")
        print("  2. Make sure Chrome browser is installed")
        print("  3. Check your internet connection")
