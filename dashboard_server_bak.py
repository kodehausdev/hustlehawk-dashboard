#!/usr/bin/env python3
"""
JobHunter Dashboard Server
Serves the web dashboard and provides job data via API
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sqlite3
from urllib.parse import urlparse, parse_qs

class JobHunterHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Serve jobs.json API
        if parsed_path.path == '/jobs.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Get jobs from database
            jobs = self.get_jobs_from_db()
            self.wfile.write(json.dumps(jobs).encode())
        
        # Serve dashboard.html
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard.html':
            self.path = '/dashboard.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        
        else:
            return SimpleHTTPRequestHandler.do_GET(self)
    
    def get_jobs_from_db(self):
        """Fetch jobs from SQLite database"""
        try:
            conn = sqlite3.connect('jobhunter.db')
            c = conn.cursor()
            
            # Updated query to include scrape_date
            c.execute('''SELECT job_id, title, company, location, match_score,
                               url, tags, description, salary, posted_date, source, scrape_date
                        FROM jobs
                        ORDER BY scrape_date DESC, match_score DESC''')
            
            jobs = []
            for row in c.fetchall():
                job = {
                    'id': row[0],
                    'title': row[1],
                    'company': row[2] or 'Unknown',
                    'location': row[3] or 'Remote',
                    'match_score': int(row[4]) if row[4] else 0,
                    'url': row[5] or '',
                    'tags': row[6].split(', ') if row[6] else [],
                    'description': row[7] or '',
                    'salary': row[8] or 'Not specified',
                    'posted_date': row[9] or '',
                    'source': row[10] or '',
                    'scrape_date': row[11] or ''
                }
                jobs.append(job)
            
            conn.close()
            return jobs
        
        except Exception as e:
            print(f"Error fetching jobs: {e}")
            return []

def main():
    PORT = 8000
    
    print("="*60)
    print(" "*15 + "🦅 HUSTLEHAWK DASHBOARD")
    print("="*60)
    print(f"\n✓ Server starting on port {PORT}...")
    print(f"\n🌐 Open your browser to:")
    print(f"   http://localhost:{PORT}/dashboard.html")
    print("\n💡 Features:")
    print("   📅 Today's jobs filter")
    print("   📆 This week filter")
    print("   🗑️  Auto-deletes jobs older than 7 days")
    print("\n💡 Tip: Keep this terminal running")
    print("   Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    server = HTTPServer(('', PORT), JobHunterHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped!")
        server.shutdown()

if __name__ == '__main__':
    main()
