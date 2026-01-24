#!/usr/bin/env python3
"""
Tennessee School Closings Scraper
Scrapes NewsChannel 5's school closings page - data is server-rendered HTML

Target structure:
<article class="closing js-block">
    <p class="text--primary js-sort-value">School Name</p>
    <p class="text--secondary">Status details</p>
</article>
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import sys

NC5_URL = "https://www.newschannel5.com/weather/school-closings-delays"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def classify_status(status_text):
    """Classify the status based on keywords"""
    text = status_text.upper()
    
    if any(kw in text for kw in ['2 HOUR', '2-HOUR', 'TWO HOUR', '1 HOUR', '1-HOUR', 'DELAY']):
        return 'DELAYED'
    elif any(kw in text for kw in ['EARLY', 'DISMISS', 'CLOSING AT', 'CLOSES AT']):
        return 'EARLY_DISMISSAL'
    elif any(kw in text for kw in ['REMOTE', 'VIRTUAL', 'DISTANCE', 'ONLINE']):
        return 'REMOTE'
    elif any(kw in text for kw in ['CLOSED', 'CANCEL', 'NO SCHOOL']):
        return 'CLOSED'
    else:
        return 'CLOSED'

def scrape_newschannel5():
    """Scrape NewsChannel 5 Nashville school closings"""
    closings = []
    
    try:
        print(f"Fetching: {NC5_URL}")
        response = requests.get(NC5_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        print(f"Status: {response.status_code}, Length: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all closing articles
        closing_articles = soup.select('article.closing')
        print(f"Found {len(closing_articles)} closings")
        
        for article in closing_articles:
            name_el = article.select_one('.text--primary')
            status_el = article.select_one('.text--secondary')
            
            if name_el:
                name = name_el.get_text(strip=True)
                status_detail = status_el.get_text(strip=True) if status_el else 'CLOSED'
                status = classify_status(status_detail)
                
                closings.append({
                    'name': name,
                    'status': status,
                    'status_detail': status_detail,
                    'region': 'Middle Tennessee',
                    'source': 'NewsChannel 5'
                })
        
    except requests.RequestException as e:
        print(f"Error fetching NewsChannel 5: {e}")
        return []
    
    return closings

def main():
    print("=" * 50)
    print("TN SCHOOL CLOSINGS SCRAPER")
    print("=" * 50)
    
    closings = scrape_newschannel5()
    
    # Count by status
    by_status = {}
    for c in closings:
        by_status[c['status']] = by_status.get(c['status'], 0) + 1
    
    # Build output
    output = {
        'meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_closings': len(closings),
            'by_status': by_status,
            'sources': ['NewsChannel 5']
        },
        'closings': closings
    }
    
    # Write JSON
    with open('closings.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nTotal: {len(closings)} closings")
    print(f"By status: {by_status}")
    print("Written to closings.json")
    
    # Exit with error if no closings found during expected weather
    # (optional - remove if you want 0 closings to be valid)
    return 0

if __name__ == '__main__':
    sys.exit(main())
