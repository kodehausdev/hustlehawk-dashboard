#!/usr/bin/env python3
"""
JobHunter Pro - Your Personal Job Application Assistant
Scrapes jobs, filters by skills, tracks applications, and more!

Author: Kode
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
import sqlite3
from urllib.parse import urlencode, quote_plus

# =============================================================================
# YOUR PROFILE DATA (Edit this section)
# =============================================================================

YOUR_PROFILE = {
    "name": "Seyi Fatoki",
    "email": "fatokiseyi0@gmail.com",
    "phone": "+234 9163315969",
    "github": "https://github.com/kodehausdev",
    "linkedin": "https://www.linkedin.com/in/seyi-fatoki-a180a3389/",
    "portfolio": "https://optipropose.com",
    "location": "Abuja, Nigeria", # Added a comma here if you missed it earlier

    # Your skills (for job matching)
    "skills": [
        "Python", "JavaScript", "React", "Node.js",
        "Firebase", "Firestore", "Git", "Linux",
        "Bash Scripting", "Web Security", "SQL",
        "Penetration Testing", "Cybersecurity",
        "Docker", "API Development", "Web Scraping"
    ],

    # Job preferences
    "job_titles": [
        "Python Developer",
        "Junior Developer",
        "Full Stack Developer",
        "Security Analyst",
        "Penetration Tester",
        "Backend Developer",
        "Software Engineer"
    ],

    "remote_only": False,  # Set to True if only remote
    "min_salary": 0,  # Minimum salary (if specified)
    "locations": ["Remote", "Lagos", "Berlin", "Abuja", "Nigeria"]
}


# =============================================================================
# DATABASE SETUP
# =============================================================================

def init_database():
    """Initialize SQLite database for tracking jobs"""
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT UNIQUE,
        title TEXT,
        company TEXT,
        location TEXT,
        salary TEXT,
        url TEXT,
        description TEXT,
        posted_date TEXT,
        source TEXT,
        match_score INTEGER,
        status TEXT DEFAULT 'found',
        applied_date TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'submitted',
        response TEXT,
        interview_date TEXT,
        notes TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized")

# =============================================================================
# JOB SCRAPERS
# =============================================================================

class JobScraper:
    """Base class for job scrapers"""
    
    def __init__(self, profile):
        self.profile = profile
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def calculate_match_score(self, job_description, job_title):
        """Calculate how well a job matches your skills (0-100)"""
        score = 0
        description_lower = job_description.lower() + " " + job_title.lower()
        
        # Check skills match
        matched_skills = 0
        for skill in self.profile['skills']:
            if skill.lower() in description_lower:
                matched_skills += 1
        
        # Calculate score
        if matched_skills > 0:
            score = min(100, int((matched_skills / len(self.profile['skills'])) * 100))
        
        return score, matched_skills
    
    def save_job(self, job_data):
        """Save job to database"""
        conn = sqlite3.connect('jobs.db')
        c = conn.cursor()
        
        try:
            c.execute('''INSERT OR IGNORE INTO jobs 
                        (job_id, title, company, location, salary, url, 
                         description, posted_date, source, match_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (job_data['job_id'], job_data['title'], job_data['company'],
                      job_data['location'], job_data['salary'], job_data['url'],
                      job_data['description'], job_data['posted_date'],
                      job_data['source'], job_data['match_score']))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving job: {e}")
            return False
        finally:
            conn.close()

class RemoteOKScraper(JobScraper):
    """Scrape jobs from RemoteOK"""
    
    def scrape(self):
        """Scrape remote jobs"""
        print("\n🔍 Scraping RemoteOK...")
        jobs = []
        
        try:
            # RemoteOK has a simple JSON API
            url = "https://remoteok.com/api"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data[1:21]:  # Skip first item (metadata), get 20 jobs
                    # Check if job matches your criteria
                    title = item.get('position', '')
                    description = item.get('description', '')
                    company = item.get('company', 'Unknown')
                    
                    # Calculate match
                    match_score, matched_skills = self.calculate_match_score(
                        description, title
                    )
                    
                    if match_score > 20:  # Only save if >20% match
                        job = {
                            'job_id': f"remoteok_{item.get('id')}",
                            'title': title,
                            'company': company,
                            'location': 'Remote',
                            'salary': item.get('salary_min', 'Not specified'),
                            'url': item.get('url', ''),
                            'description': description[:500],  # Truncate
                            'posted_date': item.get('date', ''),
                            'source': 'RemoteOK',
                            'match_score': match_score
                        }
                        
                        if self.save_job(job):
                            jobs.append(job)
                            print(f"  ✓ Found: {title} at {company} ({match_score}% match)")
                
                print(f"✓ RemoteOK: Found {len(jobs)} matching jobs")
            
        except Exception as e:
            print(f"✗ RemoteOK error: {e}")
        
        return jobs

class IndeedScraper(JobScraper):
    """Scrape jobs from Indeed"""
    
    def scrape(self, location="Remote"):
        """Scrape Indeed jobs"""
        print(f"\n🔍 Scraping Indeed ({location})...")
        jobs = []
        
        try:
            for job_title in self.profile['job_titles'][:3]:  # Search top 3 titles
                query = f"{job_title} {location}"
                url = f"https://www.indeed.com/jobs?q={quote_plus(query)}&l={quote_plus(location)}"
                
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find job cards (Indeed's structure may change)
                    job_cards = soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards[:5]:  # Top 5 per search
                        try:
                            title_elem = card.find('h2', class_='jobTitle')
                            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                            
                            company_elem = card.find('span', class_='companyName')
                            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                            
                            location_elem = card.find('div', class_='companyLocation')
                            location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                            
                            # Get job link
                            link_elem = card.find('a', class_='jcs-JobTitle')
                            job_url = "https://www.indeed.com" + link_elem['href'] if link_elem else ""
                            
                            # Calculate match (we don't have full description yet)
                            match_score, _ = self.calculate_match_score(title, title)
                            
                            job = {
                                'job_id': f"indeed_{hash(job_url)}",
                                'title': title,
                                'company': company,
                                'location': location,
                                'salary': 'Not specified',
                                'url': job_url,
                                'description': title,
                                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'Indeed',
                                'match_score': match_score
                            }
                            
                            if self.save_job(job):
                                jobs.append(job)
                                print(f"  ✓ {title} at {company}")
                        
                        except Exception as e:
                            continue
                
                time.sleep(2)  # Be respectful
            
            print(f"✓ Indeed: Found {len(jobs)} jobs")
        
        except Exception as e:
            print(f"✗ Indeed error: {e}")
        
        return jobs

class GitHubJobsScraper(JobScraper):
    """Scrape tech jobs from GitHub Jobs alternatives"""
    
    def scrape(self):
        """Scrape from We Work Remotely (GitHub Jobs alternative)"""
        print("\n🔍 Scraping We Work Remotely...")
        jobs = []
        
        try:
            url = "https://weworkremotely.com/categories/remote-programming-jobs"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                job_listings = soup.find_all('li', class_='feature')
                
                for listing in job_listings[:10]:
                    try:
                        title_elem = listing.find('span', class_='title')
                        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                        
                        company_elem = listing.find('span', class_='company')
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        
                        link_elem = listing.find('a')
                        job_url = "https://weworkremotely.com" + link_elem['href'] if link_elem else ""
                        
                        match_score, _ = self.calculate_match_score(title, title)
                        
                        if match_score > 15:
                            job = {
                                'job_id': f"wwr_{hash(job_url)}",
                                'title': title,
                                'company': company,
                                'location': 'Remote',
                                'salary': 'Not specified',
                                'url': job_url,
                                'description': title,
                                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                'source': 'WeWorkRemotely',
                                'match_score': match_score
                            }
                            
                            if self.save_job(job):
                                jobs.append(job)
                                print(f"  ✓ {title} at {company}")
                    
                    except Exception as e:
                        continue
                
                print(f"✓ WeWorkRemotely: Found {len(jobs)} jobs")
        
        except Exception as e:
            print(f"✗ WeWorkRemotely error: {e}")
        
        return jobs

# =============================================================================
# JOB TRACKER & REPORTER
# =============================================================================

def get_all_jobs(min_match_score=0, status=None):
    """Get all jobs from database"""
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE match_score >= ?"
    params = [min_match_score]
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY match_score DESC, created_at DESC"
    
    c.execute(query, params)
    
    columns = [description[0] for description in c.description]
    jobs = [dict(zip(columns, row)) for row in c.fetchall()]
    
    conn.close()
    return jobs

def mark_job_applied(job_id, notes=""):
    """Mark a job as applied"""
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    
    c.execute('''UPDATE jobs SET status='applied', 
                 applied_date=? WHERE id=?''',
             (datetime.now().strftime('%Y-%m-%d'), job_id))
    
    c.execute('''INSERT INTO applications (job_id, notes) VALUES (?, ?)''',
             (job_id, notes))
    
    conn.commit()
    conn.close()
    print(f"✓ Marked job #{job_id} as applied")

def generate_report():
    """Generate a comprehensive job search report"""
    conn = sqlite3.connect('jobs.db')
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'")
    applied = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 70")
    high_matches = c.fetchone()[0]
    
    c.execute("SELECT AVG(match_score) FROM jobs")
    avg_match = c.fetchone()[0] or 0
    
    c.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source")
    by_source = c.fetchall()
    
    conn.close()
    
    # Generate report
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║              📊 JOB SEARCH REPORT                            ║
╚══════════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
────────────────────────────────────────────────────────────────
  Total Jobs Found:        {total_jobs}
  High Match (>70%):       {high_matches}
  Applications Sent:       {applied}
  Average Match Score:     {avg_match:.1f}%
  
JOBS BY SOURCE:
────────────────────────────────────────────────────────────────
"""
    
    for source, count in by_source:
        report += f"  {source:20s} {count:3d} jobs\n"
    
    report += "\n"
    
    # Top matches
    top_jobs = get_all_jobs(min_match_score=60)[:10]
    
    if top_jobs:
        report += "TOP 10 MATCHES:\n"
        report += "────────────────────────────────────────────────────────────────\n"
        
        for i, job in enumerate(top_jobs, 1):
            status_emoji = "✓" if job['status'] == 'applied' else "○"
            report += f"{i:2d}. [{status_emoji}] {job['title'][:40]:40s} ({job['match_score']}%)\n"
            report += f"     {job['company'][:40]:40s} | {job['location']}\n"
            report += f"     {job['url']}\n\n"
    
    return report

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║              🎯 JOBHUNTER PRO v1.0                          ║")
    print("║                                                              ║")
    print("║          Your Personal Job Application Assistant            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize database
    init_database()
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. 🔍 Search for new jobs")
        print("2. 📋 View all jobs")
        print("3. ⭐ View high matches (>70%)")
        print("4. ✓  Mark job as applied")
        print("5. 📊 Generate report")
        print("6. 📈 View statistics")
        print("7. 🗑️  Clear old jobs")
        print("8. ⚙️  Update profile")
        print("0. 🚪 Exit")
        print()
        
        choice = input("Enter choice: ").strip()
        
        if choice == '1':
            # Search for jobs
            print("\n🚀 Starting job search...")
            print(f"📝 Your skills: {', '.join(YOUR_PROFILE['skills'][:5])}...")
            print(f"🎯 Looking for: {', '.join(YOUR_PROFILE['job_titles'][:3])}")
            print()
            
            total_found = 0
            
            # RemoteOK
            scraper1 = RemoteOKScraper(YOUR_PROFILE)
            jobs1 = scraper1.scrape()
            total_found += len(jobs1)
            time.sleep(2)
            
            # Indeed
            scraper2 = IndeedScraper(YOUR_PROFILE)
            jobs2 = scraper2.scrape("Remote")
            total_found += len(jobs2)
            time.sleep(2)
            
            # WeWorkRemotely
            scraper3 = GitHubJobsScraper(YOUR_PROFILE)
            jobs3 = scraper3.scrape()
            total_found += len(jobs3)
            
            print(f"\n✓ Search complete! Found {total_found} matching jobs")
            
        elif choice == '2':
            # View all jobs
            jobs = get_all_jobs()
            print(f"\n📋 All Jobs ({len(jobs)} total)\n")
            
            for i, job in enumerate(jobs[:20], 1):
                status = "✓" if job['status'] == 'applied' else "○"
                print(f"{i:2d}. [{status}] {job['title'][:45]:45s} | {job['match_score']:3d}%")
                print(f"     {job['company'][:40]:40s} | {job['source']}")
                print(f"     {job['url']}")
                print()
        
        elif choice == '3':
            # High matches
            jobs = get_all_jobs(min_match_score=70)
            print(f"\n⭐ High Match Jobs ({len(jobs)} found)\n")
            
            for i, job in enumerate(jobs, 1):
                status = "✓" if job['status'] == 'applied' else "○"
                print(f"{i:2d}. [{status}] {job['title']}")
                print(f"     Company: {job['company']}")
                print(f"     Match: {job['match_score']}%")
                print(f"     URL: {job['url']}")
                print()
        
        elif choice == '4':
            # Mark as applied
            job_id = input("Enter job ID: ").strip()
            notes = input("Notes (optional): ").strip()
            mark_job_applied(job_id, notes)
        
        elif choice == '5':
            # Generate report
            report = generate_report()
            print(report)
            
            save = input("\nSave report to file? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"job_report_{datetime.now().strftime('%Y%m%d')}.txt"
                with open(filename, 'w') as f:
                    f.write(report)
                print(f"✓ Report saved to {filename}")
        
        elif choice == '6':
            # Statistics
            jobs = get_all_jobs()
            if jobs:
                match_scores = [j['match_score'] for j in jobs]
                print(f"\n📈 Statistics:")
                print(f"  Total jobs: {len(jobs)}")
                print(f"  Avg match: {sum(match_scores)/len(match_scores):.1f}%")
                print(f"  Highest match: {max(match_scores)}%")
                print(f"  Lowest match: {min(match_scores)}%")
        
        elif choice == '0':
            print("\n👋 Happy job hunting! Good luck!")
            break
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Good luck with your job search!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
