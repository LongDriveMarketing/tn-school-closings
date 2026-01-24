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

# Official Tennessee Grand Divisions per TCA 4-1-201 through 4-1-204
WEST_COUNTIES = {
    "Benton", "Carroll", "Chester", "Crockett", "Decatur", "Dyer", "Fayette",
    "Gibson", "Hardeman", "Hardin", "Haywood", "Henderson", "Henry", "Lake",
    "Lauderdale", "Madison", "McNairy", "Obion", "Shelby", "Tipton", "Weakley"
}

EAST_COUNTIES = {
    "Anderson", "Bledsoe", "Blount", "Bradley", "Campbell", "Carter", "Claiborne",
    "Cocke", "Cumberland", "Grainger", "Greene", "Hamblen", "Hamilton", "Hancock",
    "Hawkins", "Jefferson", "Johnson", "Knox", "Loudon", "Marion", "McMinn",
    "Meigs", "Monroe", "Morgan", "Polk", "Rhea", "Roane", "Scott", "Sevier",
    "Sullivan", "Unicoi", "Union", "Washington"
}

MIDDLE_COUNTIES = {
    "Bedford", "Cannon", "Cheatham", "Clay", "Coffee", "Davidson", "DeKalb",
    "Dickson", "Fentress", "Franklin", "Giles", "Grundy", "Hickman", "Houston",
    "Humphreys", "Jackson", "Lawrence", "Lewis", "Lincoln", "Macon", "Marshall",
    "Maury", "Montgomery", "Moore", "Overton", "Perry", "Pickett", "Putnam",
    "Robertson", "Rutherford", "Sequatchie", "Smith", "Stewart", "Sumner",
    "Trousdale", "Van Buren", "Warren", "Wayne", "White", "Williamson", "Wilson"
}

# Known city-to-region mappings for schools that use city names instead of counties
CITY_REGION_MAP = {
    # Middle TN cities
    "Nashville": "Middle Tennessee",
    "Murfreesboro": "Middle Tennessee",
    "Franklin": "Middle Tennessee",
    "Clarksville": "Middle Tennessee",
    "Gallatin": "Middle Tennessee",
    "Hendersonville": "Middle Tennessee",
    "Lebanon": "Middle Tennessee",
    "Columbia": "Middle Tennessee",
    "Spring Hill": "Middle Tennessee",
    "Smyrna": "Middle Tennessee",
    "La Vergne": "Middle Tennessee",
    "Tullahoma": "Middle Tennessee",
    "Cookeville": "Middle Tennessee",
    "Shelbyville": "Middle Tennessee",
    # West TN cities
    "Memphis": "West Tennessee",
    "Jackson": "West Tennessee",
    "Bartlett": "West Tennessee",
    "Collierville": "West Tennessee",
    "Germantown": "West Tennessee",
    "Dyersburg": "West Tennessee",
    "Martin": "West Tennessee",
    "Union City": "West Tennessee",
    "Brownsville": "West Tennessee",
    # East TN cities
    "Knoxville": "East Tennessee",
    "Chattanooga": "East Tennessee",
    "Johnson City": "East Tennessee",
    "Kingsport": "East Tennessee",
    "Bristol": "East Tennessee",
    "Morristown": "East Tennessee",
    "Maryville": "East Tennessee",
    "Cleveland": "East Tennessee",
    "Oak Ridge": "East Tennessee",
    "Sevierville": "East Tennessee",
    "Gatlinburg": "East Tennessee",
    "Pigeon Forge": "East Tennessee",
}

def classify_region(name):
    """Classify school into TN region based on name"""
    name_upper = name.upper()
    
    # Check for county names
    for county in WEST_COUNTIES:
        if county.upper() in name_upper:
            return "West Tennessee"
    
    for county in EAST_COUNTIES:
        if county.upper() in name_upper:
            return "East Tennessee"
    
    for county in MIDDLE_COUNTIES:
        if county.upper() in name_upper:
            return "Middle Tennessee"
    
    # Check for city names
    for city, region in CITY_REGION_MAP.items():
        if city.upper() in name_upper:
            return region
    
    # No match - return Other
    return "Other"

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
                region = classify_region(name)
                
                closings.append({
                    'name': name,
                    'status': status,
                    'status_detail': status_detail,
                    'region': region,
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
    
    # Count by region
    by_region = {}
    for c in closings:
        by_region[c['region']] = by_region.get(c['region'], 0) + 1
    
    # Build output
    output = {
        'meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_closings': len(closings),
            'by_status': by_status,
            'by_region': by_region,
            'sources': ['NewsChannel 5']
        },
        'closings': closings
    }
    
    # Write JSON
    with open('closings.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nTotal: {len(closings)} closings")
    print(f"By status: {by_status}")
    print(f"By region: {by_region}")
    print("Written to closings.json")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
