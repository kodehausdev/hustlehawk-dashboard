#!/bin/bash
echo "🚀 Starting JobHunter Pro..."
echo ""

# Scrape new jobs
echo "📡 Fetching fresh jobs..."
python3 real_scrapers.py

echo ""
echo "🌐 Launching dashboard..."
python3 dashboard_server.py
