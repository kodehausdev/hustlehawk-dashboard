#!/usr/bin/env python3
"""
JobHunter Pro v2 - Smarter Job Search with API Support + Offline Mode
Works with official APIs, has demo mode, and can import from CSV/JSON

Author: Kode
Version: 2.0
"""

import json
import sqlite3
import random
from datetime import datetime, timedelta
import os

# =============================================================================
# CONFIGURATION
# =============================================================================

YOUR_PROFILE = {
    "name": "Kode",
    "email": "your.email@example.com",
    "location": "Abuja, Nigeria",
    "github": "github.com/yourusername",
    "portfolio": "optipropose.com",
    
    "skills": [
        "Python", "JavaScript", "React", "Node.js",
        "Firebase", "Firestore", "Linux", "Bash",
        "Cybersecurity", "Penetration Testing", "SQL",
        "Docker", "Git", "Web Security", "API Development"
    ],
    
    "experience_level": "Junior",  # Entry/Junior/Mid/Senior
    
    "job_keywords": [
        "python developer", "javascript developer",
        "full stack developer", "backend developer",
        "security analyst", "penetration tester",
        "software engineer", "junior developer",
        "react developer", "node developer"
    ],
    
    "excluded_keywords": [
        "senior only", "10+ years", "lead", "principal",
        "architect", "director"
    ]
}

# =============================================================================
# DATABASE
# =============================================================================

def init_database():
    """Initialize or connect to database"""
    conn = sqlite3.connect('jobhunter.db')
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
        requirements TEXT,
        posted_date TEXT,
        source TEXT,
        match_score INTEGER,
        status TEXT DEFAULT 'new',
        applied_date TEXT,
        notes TEXT,
        tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'submitted',
        cover_letter TEXT,
        response TEXT,
        interview_date TEXT,
        notes TEXT,
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    conn.commit()
    conn.close()

# =============================================================================
# MOCK DATA GENERATOR (For Testing/Demo)
# =============================================================================

class MockJobGenerator:
    """Generate realistic mock job postings for testing"""
    
    COMPANIES = [
        "TechCorp", "InnovateLabs", "CloudSystems", "DataFlow Inc",
        "SecureNet", "DevHub", "CodeCraft", "ByteBuilders",
        "AppGenius", "WebWorks", "FullStack Co", "CyberGuard"
    ]
    
    JOB_TITLES = [
        "Junior Python Developer",
        "Full Stack JavaScript Developer",
        "Backend Developer (Python)",
        "React Frontend Developer",
        "Junior Security Analyst",
        "DevOps Engineer",
        "Software Engineer - Entry Level",
        "Web Developer (React/Node)",
        "Junior Penetration Tester",
        "Python Backend Engineer"
    ]
    
    LOCATIONS = [
        "Remote", "Remote (US)", "Remote (Europe)", "Remote (Worldwide)",
        "Lagos, Nigeria", "Abuja, Nigeria", "Remote (Africa)",
        "Hybrid - Lagos", "Remote (GMT+1)"
    ]
    
    DESCRIPTIONS_TEMPLATES = [
        "We're seeking a talented {level} developer to join our growing team. You'll work on {tech} projects and collaborate with experienced engineers.",
        "Join our innovative team as a {level} developer! Build scalable applications using {tech} while learning from industry experts.",
        "Exciting opportunity for a {level} developer passionate about {tech}. Work on real-world projects with mentorship and growth opportunities.",
        "Looking for a motivated {level} developer with {tech} experience. Remote-first company with flexible hours and great benefits."
    ]
    
    REQUIREMENTS_TEMPLATES = [
        "• {exp} experience with {tech}\n• Strong problem-solving skills\n• Good communication\n• Git/GitHub proficiency",
        "• Proficiency in {tech}\n• {exp} of development experience\n• Understanding of REST APIs\n• Team player with good communication",
        "• Experience with {tech}\n• {exp} in software development\n• Knowledge of databases\n• Passion for clean code"
    ]
    
    def generate_jobs(self, count=50):
        """Generate mock job postings"""
        jobs = []
        
        for i in range(count):
            # Random company and title
            company = random.choice(self.COMPANIES)
            title = random.choice(self.JOB_TITLES)
            
            # Determine level
            level = "junior" if "Junior" in title or "Entry" in title else "mid-level"
            
            # Random tech stack
            tech_stacks = [
                "Python, Django, PostgreSQL",
                "JavaScript, React, Node.js",
                "Python, Flask, MongoDB",
                "React, TypeScript, Firebase",
                "Node.js, Express, MySQL",
                "Python, FastAPI, Docker"
            ]
            tech = random.choice(tech_stacks)
            
            # Generate description
            desc_template = random.choice(self.DESCRIPTIONS_TEMPLATES)
            description = desc_template.format(level=level, tech=tech)
            
            # Generate requirements
            req_template = random.choice(self.REQUIREMENTS_TEMPLATES)
            exp = random.choice(["1-2 years", "0-1 years", "Less than 1 year"])
            requirements = req_template.format(tech=tech, exp=exp)
            
            # Salary
            salaries = [
                "$40,000 - $60,000",
                "$50,000 - $70,000",
                "$35,000 - $55,000",
                "Competitive",
                "$45,000 - $65,000",
                "Not specified"
            ]
            
            # Posted date (random within last 30 days)
            days_ago = random.randint(0, 30)
            posted_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            job = {
                'job_id': f'mock_{i+1}',
                'title': title,
                'company': company,
                'location': random.choice(self.LOCATIONS),
                'salary': random.choice(salaries),
                'url': f'https://example.com/jobs/mock-{i+1}',
                'description': description,
                'requirements': requirements,
                'posted_date': posted_date,
                'source': 'Demo Data',
                'tags': tech
            }
            
            jobs.append(job)
        
        return jobs

# =============================================================================
# JOB MATCHER
# =============================================================================

class JobMatcher:
    """Match jobs against your profile"""
    
    def __init__(self, profile):
        self.profile = profile
    
    def calculate_match(self, job):
        """Calculate match score (0-100)"""
        score = 0
        reasons = []
        
        # Combine all searchable text
        searchable = (
            f"{job.get('title', '')} "
            f"{job.get('description', '')} "
            f"{job.get('requirements', '')} "
            f"{job.get('tags', '')}"
        ).lower()
        
        # Check skills match (40 points max)
        skill_matches = 0
        for skill in self.profile['skills']:
            if skill.lower() in searchable:
                skill_matches += 1
        
        if skill_matches > 0:
            skill_score = min(40, (skill_matches / len(self.profile['skills'])) * 100)
            score += skill_score
            reasons.append(f"{skill_matches} skills match")
        
        # Check job title keywords (30 points)
        title_lower = job.get('title', '').lower()
        for keyword in self.profile['job_keywords']:
            if keyword in title_lower:
                score += 30
                reasons.append(f"Title matches '{keyword}'")
                break
        
        # Check experience level (20 points)
        if self.profile['experience_level'].lower() in searchable:
            score += 20
            reasons.append("Experience level matches")
        elif 'senior' not in searchable and 'lead' not in searchable:
            score += 10
            reasons.append("Suitable experience level")
        
        # Remote preference (10 points)
        if 'remote' in job.get('location', '').lower():
            score += 10
            reasons.append("Remote position")
        
        # Check for excluded keywords (penalty)
        for excluded in self.profile['excluded_keywords']:
            if excluded in searchable:
                score = max(0, score - 20)
                reasons.append(f"⚠️ Contains '{excluded}'")
        
        return min(100, score), reasons

def save_job(job, match_score=0):
    """Save job to database"""
    conn = sqlite3.connect('jobhunter.db')
    c = conn.cursor()
    
    try:
        c.execute('''INSERT OR REPLACE INTO jobs 
                    (job_id, title, company, location, salary, url, 
                     description, requirements, posted_date, source, match_score, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (job['job_id'], job['title'], job['company'],
                  job['location'], job['salary'], job['url'],
                  job.get('description', ''), job.get('requirements', ''),
                  job['posted_date'], job['source'], match_score,
                  job.get('tags', '')))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving job: {e}")
        return False
    finally:
        conn.close()

# =============================================================================
# JOB DATABASE QUERIES
# =============================================================================

def get_jobs(min_score=0, status=None, limit=None):
    """Get jobs from database"""
    conn = sqlite3.connect('jobhunter.db')
    c = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE match_score >= ?"
    params = [min_score]
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY match_score DESC, created_at DESC"
    
    if limit:
        query += f" LIMIT {limit}"
    
    c.execute(query, params)
    
    columns = [desc[0] for desc in c.description]
    jobs = [dict(zip(columns, row)) for row in c.fetchall()]
    
    conn.close()
    return jobs

def update_job_status(job_id, status, notes=""):
    """Update job status"""
    conn = sqlite3.connect('jobhunter.db')
    c = conn.cursor()
    
    c.execute('''UPDATE jobs SET status=?, notes=?, applied_date=? 
                 WHERE id=?''',
             (status, notes, datetime.now().strftime('%Y-%m-%d'), job_id))
    
    if status == 'applied':
        c.execute('''INSERT INTO applications (job_id, notes) 
                     VALUES (?, ?)''', (job_id, notes))
    
    conn.commit()
    conn.close()

def get_statistics():
    """Get database statistics"""
    conn = sqlite3.connect('jobhunter.db')
    c = conn.cursor()
    
    stats = {}
    
    c.execute("SELECT COUNT(*) FROM jobs")
    stats['total'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE status='applied'")
    stats['applied'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 70")
    stats['high_match'] = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM jobs WHERE match_score >= 50 AND match_score < 70")
    stats['medium_match'] = c.fetchone()[0]
    
    c.execute("SELECT AVG(match_score) FROM jobs")
    stats['avg_score'] = c.fetchone()[0] or 0
    
    c.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source")
    stats['by_source'] = dict(c.fetchall())
    
    conn.close()
    return stats

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def display_job_detail(job):
    """Display full job details"""
    print("\n" + "="*80)
    print(f"📋 {job['title']}")
    print("="*80)
    print(f"🏢 Company:      {job['company']}")
    print(f"📍 Location:     {job['location']}")
    print(f"💰 Salary:       {job['salary']}")
    print(f"📅 Posted:       {job['posted_date']}")
    print(f"🎯 Match Score:  {job['match_score']}%")
    print(f"🔗 URL:          {job['url']}")
    print(f"📊 Status:       {job['status']}")
    print()
    print("📝 Description:")
    print("-" * 80)
    print(job.get('description', 'N/A'))
    print()
    print("✅ Requirements:")
    print("-" * 80)
    print(job.get('requirements', 'N/A'))
    print("="*80)

def display_job_list(jobs, show_numbers=True):
    """Display list of jobs"""
    if not jobs:
        print("  No jobs found.")
        return
    
    for i, job in enumerate(jobs, 1):
        status_emoji = {
            'new': '○',
            'interested': '⭐',
            'applied': '✓',
            'rejected': '✗',
            'interview': '🎯'
        }.get(job['status'], '○')
        
        num = f"{i:2d}. " if show_numbers else "   "
        
        print(f"{num}[{status_emoji}] {job['title'][:50]:50s} | {int(job['match_score']):3d}%")
        print(f"     {job['company'][:35]:35s} | {job['location'][:20]:20s}")
        
        if job['status'] != 'new':
            print(f"     Status: {job['status']}")
        print()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def generate_demo_data():
    """Generate demo jobs for testing"""
    print("🎲 Generating demo job data...")
    
    generator = MockJobGenerator()
    matcher = JobMatcher(YOUR_PROFILE)
    
    jobs = generator.generate_jobs(50)
    
    saved = 0
    for job in jobs:
        score, reasons = matcher.calculate_match(job)
        if save_job(job, score):
            saved += 1
    
    print(f"✓ Generated and saved {saved} demo jobs")
    return saved

def main_menu():
    """Main application menu"""
    while True:
        print("\n" + "="*80)
        print(" "*25 + "🎯 JOBHUNTER PRO v2.0")
        print("="*80)
        
        stats = get_statistics()
        
        print(f"\n📊 Quick Stats: {stats['total']} jobs | "
              f"{stats['high_match']} high matches | "
              f"{stats['applied']} applied")
        
        print("\n1.  🔍 Generate Demo Jobs (Offline Testing)")
        print("2.  📋 View All Jobs")
        print("3.  ⭐ High Matches (70%+)")
        print("4.  🎯 Medium Matches (50-69%)")
        print("5.  🔎 Search Jobs")
        print("6.  👁️  View Job Details")
        print("7.  ✓  Mark as Applied")
        print("8.  ⭐ Mark as Interested")
        print("9.  📊 Statistics & Report")
        print("10. 📤 Export Jobs to CSV")
        print("11. 📥 Import Jobs from File")
        print("12. 🗑️  Delete Old Jobs")
        print("0.  🚪 Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            # Generate demo data
            count = input("How many jobs to generate? (default 50): ").strip()
            count = int(count) if count.isdigit() else 50
            
            generator = MockJobGenerator()
            matcher = JobMatcher(YOUR_PROFILE)
            
            jobs = generator.generate_jobs(count)
            saved = 0
            
            for job in jobs:
                score, reasons = matcher.calculate_match(job)
                if score > 20:  # Only save if some match
                    if save_job(job, score):
                        saved += 1
            
            print(f"\n✓ Generated {saved} jobs with match scores!")
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            # View all
            jobs = get_jobs(limit=30)
            print(f"\n📋 All Jobs (showing {len(jobs)})\n")
            display_job_list(jobs)
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            # High matches
            jobs = get_jobs(min_score=70)
            print(f"\n⭐ High Match Jobs ({len(jobs)} found)\n")
            display_job_list(jobs)
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            # Medium matches
            jobs = get_jobs(min_score=50)
            jobs = [j for j in jobs if j['match_score'] < 70]
            print(f"\n🎯 Medium Match Jobs ({len(jobs)} found)\n")
            display_job_list(jobs)
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            # Search
            keyword = input("Search keyword: ").strip().lower()
            jobs = get_jobs()
            
            results = [j for j in jobs if keyword in j['title'].lower() 
                       or keyword in j['company'].lower()]
            
            print(f"\n🔎 Search Results ({len(results)} found)\n")
            display_job_list(results)
            input("\nPress Enter to continue...")
        
        elif choice == '6':
            # View details
            job_id = input("Enter job ID: ").strip()
            
            conn = sqlite3.connect('jobhunter.db')
            c = conn.cursor()
            c.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
            
            row = c.fetchone()
            if row:
                columns = [desc[0] for desc in c.description]
                job = dict(zip(columns, row))
                display_job_detail(job)
            else:
                print("Job not found!")
            
            conn.close()
            input("\nPress Enter to continue...")
        
        elif choice == '7':
            # Mark applied
            job_id = input("Enter job ID: ").strip()
            notes = input("Notes (optional): ").strip()
            
            update_job_status(job_id, 'applied', notes)
            print("✓ Marked as applied!")
            input("\nPress Enter to continue...")
        
        elif choice == '8':
            # Mark interested
            job_id = input("Enter job ID: ").strip()
            update_job_status(job_id, 'interested')
            print("✓ Marked as interested!")
            input("\nPress Enter to continue...")
        
        elif choice == '9':
            # Statistics
            stats = get_statistics()
            
            print("\n" + "="*80)
            print(" "*30 + "📊 STATISTICS")
            print("="*80)
            print(f"\nTotal Jobs:          {stats['total']}")
            print(f"High Matches (70%+): {stats['high_match']}")
            print(f"Medium Matches:      {stats['medium_match']}")
            print(f"Applied:             {stats['applied']}")
            print(f"Average Score:       {stats['avg_score']:.1f}%")
            
            if stats['by_source']:
                print("\nJobs by Source:")
                for source, count in stats['by_source'].items():
                    print(f"  {source:20s} {count:3d} jobs")
            
            print("="*80)
            input("\nPress Enter to continue...")
        
        elif choice == '10':
            # Export CSV
            jobs = get_jobs()
            
            with open('jobs_export.csv', 'w') as f:
                f.write("ID,Title,Company,Location,Salary,Match,Status,URL\n")
                for job in jobs:
                    f.write(f"{job['id']},\"{job['title']}\",\"{job['company']}\","
                           f"\"{job['location']}\",\"{job['salary']}\","
                           f"{job['match_score']},{job['status']},\"{job['url']}\"\n")
            
            print(f"✓ Exported {len(jobs)} jobs to jobs_export.csv")
            input("\nPress Enter to continue...")
        
        elif choice == '0':
            print("\n👋 Good luck with your job search!")
            break
        
        else:
            print("Invalid choice!")
            time.sleep(1)

def main():
    """Entry point"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║              🎯 JOBHUNTER PRO v2.0                          ║")
    print("║                                                              ║")
    print("║          Smart Job Search with Offline Mode                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    init_database()
    
    # Check if database is empty
    stats = get_statistics()
    
    if stats['total'] == 0:
        print("📂 Database is empty!")
        print("\nOptions:")
        print("1. Generate demo jobs for testing")
        print("2. Import from file")
        print("3. Skip (you can do this later)")
        
        choice = input("\nChoice: ").strip()
        
        if choice == '1':
            generate_demo_data()
    
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Happy job hunting!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
