#!/usr/bin/env python3
"""
Auto-Fill Job Application Helper
Generates pre-filled application data for quick submissions
"""

YOUR_DATA = {
    "personal": {
        "first_name": "Seyi",
        "last_name": "Fatoki",
        "email": "hi.kodehaus@gmail.com",
        "phone": "+234-9163315969",
        "linkedin": "https://www.linkedin.com/in/seyi-fatoki-a180a3389",
        "github": "https://github.com/kodehausdev",
        "portfolio": "optipropose.com",
        "location": "Abuja, Nigeria"
    },
    
    "experience": [
        {
            "title": "Full Stack Developer",
            "company": "OptiPropose",
            "duration": "2020 - Present",
            "description": "Built secure web applications using React, Firebase, and Node.js. Implemented Firestore security rules achieving 95/100 security score."
        }
    ],
    
    "education": {
        "degree": "political science",
        "school": "University of Abuja",
        "year": "2016-2021",
    },
    
    "cover_letter_template": """
Dear Hiring Manager,

I am excited to apply for the {job_title} position at {company}. With hands-on experience in {relevant_skills}, I am confident I can contribute to your team.

Key highlights:
- Developed production web applications with React and Firebase
- Implemented security best practices achieving 95/100 security score
- Experience with {tech_stack}
- Strong problem-solving and Linux/scripting automation skills

I'm particularly drawn to {company} because {why_company}.

I look forward to discussing how my skills align with your needs.

Best regards,
{your_name}
    """,
    
    "skills_summary": """
Technical Skills:
- Languages: Python, JavaScript, Bash
- Frontend: React, HTML/CSS
- Backend: Node.js, Firebase, Firestore
- Security: Penetration Testing, SQL Injection, Web Security
- Tools: Git, Linux, Docker, Burp Suite
- Other: Web Scraping, Automation, API Development
    """
}

def generate_cover_letter(job_title, company, tech_stack=""):
    """Generate customized cover letter"""
    relevant_skills = "Python, JavaScript, React, and cybersecurity"
    why_company = "of your innovative approach to technology"
    
    letter = YOUR_DATA["cover_letter_template"].format(
        job_title=job_title,
        company=company,
        relevant_skills=relevant_skills,
        tech_stack=tech_stack or "modern web technologies",
        why_company=why_company,
        your_name=YOUR_DATA["personal"]["first_name"] + " " + YOUR_DATA["personal"]["last_name"]
    )
    
    return letter

def export_application_data(filename="application_data.json"):
    """Export data in JSON format for easy copying"""
    import json
    
    with open(filename, 'w') as f:
        json.dump(YOUR_DATA, f, indent=2)
    
    print(f"✓ Application data exported to {filename}")

if __name__ == "__main__":
    print("=== Job Application Auto-Filler ===\n")
    
    job_title = input("Job title: ")
    company = input("Company name: ")
    tech = input("Tech stack (optional): ")
    
    print("\n" + "="*60)
    print("GENERATED COVER LETTER:")
    print("="*60)
    print(generate_cover_letter(job_title, company, tech))
    print("="*60)
    
    export_application_data()
