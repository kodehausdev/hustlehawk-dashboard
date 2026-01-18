# FILE 3: dashboard_server.py (Updated for Render)
"""
#!/usr/bin/env python3
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sqlite3

PORT = int(os.environ.get('PORT', 8000))

class JobHunterHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/jobs.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            jobs = self.get_jobs_from_db()
            self.wfile.write(json.dumps(jobs).encode())
        
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard.html':
            self.path = '/dashboard.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        
        else:
            return SimpleHTTPRequestHandler.do_GET(self)
    
    def get_jobs_from_db(self):
        try:
            conn = sqlite3.connect('jobhunter.db')
            c = conn.cursor()
            
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
            print(f"Error: {e}")
            return []

if __name__ == '__main__':
    print(f"🦅 HustleHawk Dashboard running on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), JobHunterHandler)
    server.serve_forever()
"""
