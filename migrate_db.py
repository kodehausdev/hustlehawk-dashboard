#!/usr/bin/env python3
"""
Database Migration Script
Adds scrape_date column to existing jobs table
"""
import sqlite3
from datetime import datetime

def migrate_database():
    """Add scrape_date column to jobs table"""
    
    print("="*60)
    print("  🔧 DATABASE MIGRATION - Adding scrape_date column")
    print("="*60)
    
    try:
        conn = sqlite3.connect('jobhunter.db')
        c = conn.cursor()
        
        # Check if column already exists
        c.execute("PRAGMA table_info(jobs)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'scrape_date' in columns:
            print("\n✓ scrape_date column already exists!")
        else:
            print("\n📝 Adding scrape_date column...")
            
            # Add the column
            c.execute("ALTER TABLE jobs ADD COLUMN scrape_date TEXT")
            
            # Set today's date for all existing jobs
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute("UPDATE jobs SET scrape_date = ? WHERE scrape_date IS NULL", (today,))
            
            conn.commit()
            print(f"✓ Column added successfully!")
            print(f"✓ Set scrape_date = {today} for existing jobs")
        
        # Show table structure
        print("\n📊 Current table structure:")
        c.execute("PRAGMA table_info(jobs)")
        for col in c.fetchall():
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Migration complete! You can now run the scraper.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        print("\nTry manually:")
        print("  python3 -c \"import sqlite3; conn = sqlite3.connect('jobhunter.db'); conn.execute('ALTER TABLE jobs ADD COLUMN scrape_date TEXT'); conn.commit()\"")

if __name__ == '__main__':
    migrate_database()
