#!/usr/bin/env python3
"""
Tennessee School Closings Scraper
Scrapes multiple TN news sources for school closings data.

Sources:
- NewsChannel 5 Nashville (Middle TN) - Scripps - requests
- Action News 5 Memphis (West TN) - Gray Media - Playwright
- WVLT Knoxville (East TN) - Gray Media - Playwright

Requires: pip install requests beautifulsoup4 playwright
Setup: playwright install chromium
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import sys

# Try to import playwright, fall back gracefully if not available
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Gray Media sources will be skipped.")
    print("Install with: pip install playwright && playwright install chromium")

# Source URLs
NC5_URL = "https://www.newschannel5.com/weather/school-closings-delays"
AN5_URL = "https://www.actionnews5.com/weather/closings/"
WVLT_URL = "https://www.wvlt.tv/weather/closings/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# =============================================================================
# REGION MAPPINGS
# =============================================================================

DISTRICT_TO_REGION = {
    # -------------------------------------------------------------------------
    # EAST TENNESSEE
    # -------------------------------------------------------------------------
    "Anderson County Schools": "East Tennessee",
    "Clinton City Schools": "East Tennessee",
    "Oak Ridge City Schools": "East Tennessee",
    "Bledsoe County Schools": "East Tennessee",
    "Alcoa City Schools": "East Tennessee",
    "Blount County Schools": "East Tennessee",
    "Maryville City Schools": "East Tennessee",
    "Bradley County Schools": "East Tennessee",
    "Cleveland City Schools": "East Tennessee",
    "Campbell County Schools": "East Tennessee",
    "Carter County Schools": "East Tennessee",
    "Elizabethton City Schools": "East Tennessee",
    "Claiborne County Schools": "East Tennessee",
    "Cocke County Schools": "East Tennessee",
    "Newport City Schools": "East Tennessee",
    "Cumberland County Schools": "East Tennessee",
    "Grainger County Schools": "East Tennessee",
    "Greene County Schools": "East Tennessee",
    "Greeneville City Schools": "East Tennessee",
    "Hamblen County Schools": "East Tennessee",
    "Morristown City Schools": "East Tennessee",
    "Hamilton County Schools": "East Tennessee",
    "Hamilton County Department of Education": "East Tennessee",
    "Hancock County Schools": "East Tennessee",
    "Hawkins County Schools": "East Tennessee",
    "Rogersville City Schools": "East Tennessee",
    "Jefferson County Schools": "East Tennessee",
    "Johnson County Schools": "East Tennessee",
    "Knox County Schools": "East Tennessee",
    "Loudon County Schools": "East Tennessee",
    "Lenoir City Schools": "East Tennessee",
    "Marion County Schools": "East Tennessee",
    "McMinn County Schools": "East Tennessee",
    "Athens City Schools": "East Tennessee",
    "Etowah City Schools": "East Tennessee",
    "Meigs County Schools": "East Tennessee",
    "Monroe County Schools": "East Tennessee",
    "Sweetwater City Schools": "East Tennessee",
    "Morgan County Schools": "East Tennessee",
    "Polk County Schools": "East Tennessee",
    "Rhea County Schools": "East Tennessee",
    "Dayton City Schools": "East Tennessee",
    "Roane County Schools": "East Tennessee",
    "Scott County Schools": "East Tennessee",
    "Sevier County Schools": "East Tennessee",
    "Sullivan County Schools": "East Tennessee",
    "Bristol Tennessee City Schools": "East Tennessee",
    "Bristol City Schools": "East Tennessee",
    "Kingsport City Schools": "East Tennessee",
    "Unicoi County Schools": "East Tennessee",
    "Union County Schools": "East Tennessee",
    "Washington County Schools": "East Tennessee",
    "Johnson City Schools": "East Tennessee",
    # East TN Private Schools
    "Maryville Christian School": "East Tennessee",
    "Maryville College": "East Tennessee",
    "Legacy Christian Academy": "East Tennessee",
    "Cleveland State College": "East Tennessee",
    "Cleveland State Community College": "East Tennessee",
    
    # -------------------------------------------------------------------------
    # MIDDLE TENNESSEE
    # -------------------------------------------------------------------------
    "Bedford County Schools": "Middle Tennessee",
    "Cannon County Schools": "Middle Tennessee",
    "Cheatham County Schools": "Middle Tennessee",
    "Clay County Schools": "Middle Tennessee",
    "Coffee County Schools": "Middle Tennessee",
    "Manchester City Schools": "Middle Tennessee",
    "Manchester City Sch.": "Middle Tennessee",
    "Tullahoma City Schools": "Middle Tennessee",
    "Tullahoma City Sch.": "Middle Tennessee",
    "Achievement School District": "Middle Tennessee",
    "Metropolitan Nashville Public Schools": "Middle Tennessee",
    "Metro Nashville Public Schools": "Middle Tennessee",
    "MNPS": "Middle Tennessee",
    "Tennessee Public Charter School Commission": "Middle Tennessee",
    "Dekalb County Schools": "Middle Tennessee",
    "DeKalb County Schools": "Middle Tennessee",
    "Dickson County Schools": "Middle Tennessee",
    "Fentress County Schools": "Middle Tennessee",
    "Alvin C. York Agricultural Institute": "Middle Tennessee",
    "Franklin County Schools": "Middle Tennessee",
    "Giles County Schools": "Middle Tennessee",
    "Grundy County Schools": "Middle Tennessee",
    "Hickman County Schools": "Middle Tennessee",
    "Houston County Schools": "Middle Tennessee",
    "Humphreys County Schools": "Middle Tennessee",
    "Jackson County Schools": "Middle Tennessee",
    "Lawrence County Schools": "Middle Tennessee",
    "Lewis County Schools": "Middle Tennessee",
    "Lincoln County Schools": "Middle Tennessee",
    "Fayetteville City Schools": "Middle Tennessee",
    "Macon County Schools": "Middle Tennessee",
    "Marshall County Schools": "Middle Tennessee",
    "Maury County Schools": "Middle Tennessee",
    "Maury County Public Schools": "Middle Tennessee",
    "Columbia City Schools": "Middle Tennessee",
    "Montgomery County Schools": "Middle Tennessee",
    "Clarksville-Montgomery County Schools": "Middle Tennessee",
    "Clarksville-Montgomery County School System": "Middle Tennessee",
    "CMCSS": "Middle Tennessee",
    "Moore County Schools": "Middle Tennessee",
    "Overton County Schools": "Middle Tennessee",
    "Perry County Schools": "Middle Tennessee",
    "Pickett County Schools": "Middle Tennessee",
    "Putnam County Schools": "Middle Tennessee",
    "Putnam County School System": "Middle Tennessee",
    "Robertson County Schools": "Middle Tennessee",
    "Rutherford County Schools": "Middle Tennessee",
    "Murfreesboro City Schools": "Middle Tennessee",
    "Sequatchie County Schools": "Middle Tennessee",
    "Smith County Schools": "Middle Tennessee",
    "Stewart County Schools": "Middle Tennessee",
    "Sumner County Schools": "Middle Tennessee",
    "Trousdale County Schools": "Middle Tennessee",
    "Van Buren County Schools": "Middle Tennessee",
    "Warren County Schools": "Middle Tennessee",
    "Wayne County Schools": "Middle Tennessee",
    "White County Schools": "Middle Tennessee",
    "Williamson County Schools": "Middle Tennessee",
    "Franklin Special School District": "Middle Tennessee",
    "Wilson County Schools": "Middle Tennessee",
    "Lebanon Special School District": "Middle Tennessee",
    # Middle TN Private/Other
    "Lancaster Academy": "Middle Tennessee",
    "Lancaster Early Learn. Centers": "Middle Tennessee",
    "Redeemer Academy": "Middle Tennessee",
    "St. Patrick": "Middle Tennessee",
    "Trevecca Nazarene University": "Middle Tennessee",
    "TriStar Cottage & Homeschool Co-op": "Middle Tennessee",
    "Clarksville Christian": "Middle Tennessee",
    "Lead Acad.-Goodlettsville": "Middle Tennessee",
    "Nashville State-Clarksville": "Middle Tennessee",
    "Nashville State-Dickson": "Middle Tennessee",
    "Nashville State-Humphreys Co.": "Middle Tennessee",
    "Nashville State-North Davidson": "Middle Tennessee",
    "Nashville State-Southeast": "Middle Tennessee",
    "Nashville State-White Bridge": "Middle Tennessee",
    "Franklin Spec. Sch. Dist.": "Middle Tennessee",
    "Gen. Sessions Court-Davidson Co.": "Middle Tennessee",
    
    # -------------------------------------------------------------------------
    # WEST TENNESSEE
    # -------------------------------------------------------------------------
    "Benton County Schools": "West Tennessee",
    "Hollow Rock-Bruceton Special School District": "West Tennessee",
    "Huntingdon Special Schools": "West Tennessee",
    "McKenzie Special School District": "West Tennessee",
    "South Carroll Special School District": "West Tennessee",
    "West Carroll Special School District": "West Tennessee",
    "Carroll County Schools": "West Tennessee",
    "Chester County Schools": "West Tennessee",
    "Alamo City Schools": "West Tennessee",
    "Bells City Schools": "West Tennessee",
    "Bells City School": "West Tennessee",
    "Crockett County Schools": "West Tennessee",
    "Decatur County Schools": "West Tennessee",
    "Dyer County Schools": "West Tennessee",
    "Dyersburg City Schools": "West Tennessee",
    "Fayette County Schools": "West Tennessee",
    "Fayette County Public Schools": "West Tennessee",
    "Bradford Special Schools": "West Tennessee",
    "Gibson County Special School District": "West Tennessee",
    "Humboldt City Schools": "West Tennessee",
    "Milan Special School District": "West Tennessee",
    "Trenton City Schools": "West Tennessee",
    "Hardeman County Schools": "West Tennessee",
    "Hardin County Schools": "West Tennessee",
    "Haywood County Schools": "West Tennessee",
    "Henderson County Schools": "West Tennessee",
    "Lexington City Schools": "West Tennessee",
    "Henry County Schools": "West Tennessee",
    "Paris Special School District": "West Tennessee",
    "Lake County Schools": "West Tennessee",
    "Lauderdale County Schools": "West Tennessee",
    "Madison County Schools": "West Tennessee",
    "Jackson-Madison County Schools": "West Tennessee",
    "Jackson-Madison County School System": "West Tennessee",
    "McNairy County Schools": "West Tennessee",
    "Obion County Schools": "West Tennessee",
    "Union City Schools": "West Tennessee",
    "Shelby County Schools": "West Tennessee",
    "Memphis-Shelby County Schools": "West Tennessee",
    "Memphis Shelby County Schools": "West Tennessee",
    "Arlington Community Schools": "West Tennessee",
    "Bartlett City Schools": "West Tennessee",
    "Collierville Schools": "West Tennessee",
    "Collierville School District": "West Tennessee",
    "Germantown Municipal School District": "West Tennessee",
    "Lakeland School System": "West Tennessee",
    "Millington Municipal Schools": "West Tennessee",
    "Tipton County Schools": "West Tennessee",
    "Covington City Schools": "West Tennessee",
    "Weakley County Schools": "West Tennessee",
    # West TN Private Schools & Colleges
    "Briarcrest Christian School": "West Tennessee",
    "Christian Brothers High School": "West Tennessee",
    "Evangelical Christian School": "West Tennessee",
    "St. Benedict at Auburndale": "West Tennessee",
    "St. Benedict at Aurburndale High School": "West Tennessee",
    "Woodland Presbyterian School": "West Tennessee",
    "Immanuel Lutheran School": "West Tennessee",
    "Christ the King Lutheran School": "West Tennessee",
    "First Assembly Christian School": "West Tennessee",
    "New Hope Christian Academy": "West Tennessee",
    "Compass Community Schools": "West Tennessee",
    "Concord Academy": "West Tennessee",
    "Freedom Preparatory Academy": "West Tennessee",
    "Freedom Prep Academy": "West Tennessee",
    "KIPP Memphis Public Schools": "West Tennessee",
    "Power Center Academy": "West Tennessee",
    "STAR Academy Charter School": "West Tennessee",
    "Magnolia Heights": "West Tennessee",
    "Pleasant View School": "West Tennessee",
    "Nova Life Coach Academy": "West Tennessee",
    "Expanded Educational Services Success Academy": "West Tennessee",
    "Rhodes College": "West Tennessee",
    "University of Memphis": "West Tennessee",
    "Mid-America Baptist Theological Seminary": "West Tennessee",
    "LeMoyne-Owen College": "West Tennessee",
    # Mississippi schools (Memphis market)
    "Lafayette County School District": "West Tennessee",
    "Oxford School District": "West Tennessee",
    "Senatobia Municipal School District": "West Tennessee",
    "South Panola School District": "West Tennessee",
    "Tate County School District": "West Tennessee",
    "Northwest Mississippi Community College": "West Tennessee",
    "University of Mississippi": "West Tennessee",
}

COUNTY_REGIONS = {
    # East TN
    "Anderson": "East Tennessee", "Bledsoe": "East Tennessee", "Blount": "East Tennessee",
    "Bradley": "East Tennessee", "Campbell": "East Tennessee", "Carter": "East Tennessee",
    "Claiborne": "East Tennessee", "Cocke": "East Tennessee", "Cumberland": "East Tennessee",
    "Grainger": "East Tennessee", "Greene": "East Tennessee", "Hamblen": "East Tennessee",
    "Hamilton": "East Tennessee", "Hancock": "East Tennessee", "Hawkins": "East Tennessee",
    "Jefferson": "East Tennessee", "Johnson": "East Tennessee", "Knox": "East Tennessee",
    "Loudon": "East Tennessee", "Marion": "East Tennessee", "McMinn": "East Tennessee",
    "Meigs": "East Tennessee", "Monroe": "East Tennessee", "Morgan": "East Tennessee",
    "Polk": "East Tennessee", "Rhea": "East Tennessee", "Roane": "East Tennessee",
    "Scott": "East Tennessee", "Sevier": "East Tennessee", "Sullivan": "East Tennessee",
    "Unicoi": "East Tennessee", "Union": "East Tennessee", "Washington": "East Tennessee",
    # Middle TN
    "Bedford": "Middle Tennessee", "Cannon": "Middle Tennessee", "Cheatham": "Middle Tennessee",
    "Clay": "Middle Tennessee", "Coffee": "Middle Tennessee", "Davidson": "Middle Tennessee",
    "DeKalb": "Middle Tennessee", "Dickson": "Middle Tennessee", "Fentress": "Middle Tennessee",
    "Franklin": "Middle Tennessee", "Giles": "Middle Tennessee", "Grundy": "Middle Tennessee",
    "Hickman": "Middle Tennessee", "Houston": "Middle Tennessee", "Humphreys": "Middle Tennessee",
    "Jackson": "Middle Tennessee", "Lawrence": "Middle Tennessee", "Lewis": "Middle Tennessee",
    "Lincoln": "Middle Tennessee", "Macon": "Middle Tennessee", "Marshall": "Middle Tennessee",
    "Maury": "Middle Tennessee", "Montgomery": "Middle Tennessee", "Moore": "Middle Tennessee",
    "Overton": "Middle Tennessee", "Perry": "Middle Tennessee", "Pickett": "Middle Tennessee",
    "Putnam": "Middle Tennessee", "Robertson": "Middle Tennessee", "Rutherford": "Middle Tennessee",
    "Sequatchie": "Middle Tennessee", "Smith": "Middle Tennessee", "Stewart": "Middle Tennessee",
    "Sumner": "Middle Tennessee", "Trousdale": "Middle Tennessee", "Van Buren": "Middle Tennessee",
    "Warren": "Middle Tennessee", "Wayne": "Middle Tennessee", "White": "Middle Tennessee",
    "Williamson": "Middle Tennessee", "Wilson": "Middle Tennessee",
    # West TN
    "Benton": "West Tennessee", "Carroll": "West Tennessee", "Chester": "West Tennessee",
    "Crockett": "West Tennessee", "Decatur": "West Tennessee", "Dyer": "West Tennessee",
    "Fayette": "West Tennessee", "Gibson": "West Tennessee", "Hardeman": "West Tennessee",
    "Hardin": "West Tennessee", "Haywood": "West Tennessee", "Henderson": "West Tennessee",
    "Henry": "West Tennessee", "Lake": "West Tennessee", "Lauderdale": "West Tennessee",
    "Madison": "West Tennessee", "McNairy": "West Tennessee", "Obion": "West Tennessee",
    "Shelby": "West Tennessee", "Tipton": "West Tennessee", "Weakley": "West Tennessee",
    "Lafayette": "West Tennessee", "Panola": "West Tennessee", "Tate": "West Tennessee",
    "DeSoto": "West Tennessee", "Marshall": "West Tennessee",
}

CITY_REGIONS = {
    # East TN
    "Knoxville": "East Tennessee", "Chattanooga": "East Tennessee", "Johnson City": "East Tennessee",
    "Kingsport": "East Tennessee", "Bristol": "East Tennessee", "Morristown": "East Tennessee",
    "Cleveland": "East Tennessee", "Maryville": "East Tennessee", "Oak Ridge": "East Tennessee",
    "Athens": "East Tennessee", "Greeneville": "East Tennessee", "Elizabethton": "East Tennessee",
    "Sevierville": "East Tennessee", "Pigeon Forge": "East Tennessee", "Gatlinburg": "East Tennessee",
    # Middle TN
    "Nashville": "Middle Tennessee", "Murfreesboro": "Middle Tennessee", "Franklin": "Middle Tennessee",
    "Clarksville": "Middle Tennessee", "Columbia": "Middle Tennessee", "Gallatin": "Middle Tennessee",
    "Hendersonville": "Middle Tennessee", "Lebanon": "Middle Tennessee", "Cookeville": "Middle Tennessee",
    "Shelbyville": "Middle Tennessee", "Tullahoma": "Middle Tennessee", "Manchester": "Middle Tennessee",
    "Dickson": "Middle Tennessee", "Springfield": "Middle Tennessee", "Portland": "Middle Tennessee",
    "Smyrna": "Middle Tennessee", "La Vergne": "Middle Tennessee", "Spring Hill": "Middle Tennessee",
    "Goodlettsville": "Middle Tennessee", "White House": "Middle Tennessee", "McMinnville": "Middle Tennessee",
    # West TN
    "Memphis": "West Tennessee", "Jackson": "West Tennessee", "Bartlett": "West Tennessee",
    "Collierville": "West Tennessee", "Germantown": "West Tennessee", "Dyersburg": "West Tennessee",
    "Millington": "West Tennessee", "Covington": "West Tennessee", "Ripley": "West Tennessee",
    "Savannah": "West Tennessee", "Selmer": "West Tennessee", "Bolivar": "West Tennessee",
    "Lexington": "West Tennessee", "Henderson": "West Tennessee", "Humboldt": "West Tennessee",
    "Milan": "West Tennessee", "Trenton": "West Tennessee", "Union City": "West Tennessee",
    "Paris": "West Tennessee", "Martin": "West Tennessee", "McKenzie": "West Tennessee",
    "Oxford": "West Tennessee", "Senatobia": "West Tennessee",
}


def classify_region(name):
    """Classify school/district into TN region."""
    name_clean = name.strip()
    name_upper = name_clean.upper()
    
    # 1. Exact match
    if name_clean in DISTRICT_TO_REGION:
        return DISTRICT_TO_REGION[name_clean]
    
    # 2. Partial match
    for district, region in DISTRICT_TO_REGION.items():
        if district.upper() in name_upper or name_upper in district.upper():
            return region
    
    # 3. County match
    for county, region in COUNTY_REGIONS.items():
        if county.upper() in name_upper:
            return region
    
    # 4. City match
    for city, region in CITY_REGIONS.items():
        if city.upper() in name_upper:
            return region
    
    return "Other"


def classify_status(status_text):
    """Classify status based on keywords."""
    text = status_text.upper()
    
    if any(kw in text for kw in ['2 HOUR', '2-HOUR', 'TWO HOUR', '1 HOUR', '1-HOUR', 'DELAY']):
        return 'DELAYED'
    elif any(kw in text for kw in ['EARLY', 'DISMISS', 'CLOSING AT', 'CLOSES AT']):
        return 'EARLY_DISMISSAL'
    elif any(kw in text for kw in ['REMOTE', 'VIRTUAL', 'DISTANCE', 'ONLINE']):
        return 'REMOTE'
    elif any(kw in text for kw in ['CLOSED', 'CANCEL', 'NO SCHOOL', 'THROUGH']):
        return 'CLOSED'
    else:
        return 'CLOSED'


def scrape_newschannel5():
    """Scrape NewsChannel 5 Nashville (Middle TN) - Scripps platform."""
    closings = []
    
    try:
        print(f"Fetching: {NC5_URL}")
        response = requests.get(NC5_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        print(f"Status: {response.status_code}, Length: {len(response.text)} bytes")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        closing_articles = soup.select('article.closing')
        print(f"Found {len(closing_articles)} closings from NewsChannel 5")
        
        for article in closing_articles:
            name_el = article.select_one('.text--primary')
            status_el = article.select_one('.text--secondary')
            
            if name_el:
                name = name_el.get_text(strip=True)
                status_detail = status_el.get_text(strip=True) if status_el else 'CLOSED'
                
                closings.append({
                    'name': name,
                    'status': classify_status(status_detail),
                    'status_detail': status_detail,
                    'region': classify_region(name),
                    'source': 'NewsChannel 5'
                })
        
    except requests.RequestException as e:
        print(f"Error fetching NewsChannel 5: {e}")
    
    return closings


def scrape_gray_media(url, source_name):
    """Scrape Gray Media stations (Action News 5, WVLT) using Playwright."""
    closings = []
    
    if not PLAYWRIGHT_AVAILABLE:
        print(f"Skipping {source_name}: Playwright not available")
        return closings
    
    try:
        print(f"Fetching with Playwright: {url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for table to populate
            page.wait_for_selector('table.table tbody tr', timeout=10000)
            
            # Get page content after JS renders
            content = page.content()
            browser.close()
        
        soup = BeautifulSoup(content, 'html.parser')
        rows = soup.select('table.table tbody tr')
        print(f"Found {len(rows)} closings from {source_name}")
        
        for row in rows:
            name_el = row.select_one('td.organization span.d-block')
            status_el = row.select_one('td.status span.closings-status')
            comments_el = row.select_one('td.status span.closings-comments')
            type_el = row.select_one('td.type span')
            
            if name_el:
                name = name_el.get_text(strip=True)
                status_text = status_el.get_text(strip=True) if status_el else 'CLOSED'
                comments = comments_el.get_text(strip=True) if comments_el else ''
                org_type = type_el.get_text(strip=True) if type_el else ''
                
                status_detail = f"{status_text} - {comments}" if comments else status_text
                
                # Only include Schools and Colleges
                if org_type in ['Schools', 'Colleges', '']:
                    closings.append({
                        'name': name,
                        'status': classify_status(status_text),
                        'status_detail': status_detail,
                        'region': classify_region(name),
                        'source': source_name
                    })
        
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return closings


def deduplicate_closings(closings):
    """Remove duplicates, keeping most detailed entry."""
    seen = {}
    
    for closing in closings:
        key = closing['name'].upper().strip()
        
        if key not in seen:
            seen[key] = closing
        elif len(closing['status_detail']) > len(seen[key]['status_detail']):
            seen[key] = closing
    
    return list(seen.values())


def main():
    print("=" * 60)
    print("TN SCHOOL CLOSINGS SCRAPER")
    print(f"Run time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    all_closings = []
    sources_used = []
    
    # Middle TN - NewsChannel 5 (Scripps)
    print("\n--- NewsChannel 5 (Middle TN) ---")
    nc5 = scrape_newschannel5()
    if nc5:
        all_closings.extend(nc5)
        sources_used.append('NewsChannel 5')
    
    # West TN - Action News 5 (Gray)
    print("\n--- Action News 5 (West TN) ---")
    an5 = scrape_gray_media(AN5_URL, 'Action News 5')
    if an5:
        all_closings.extend(an5)
        sources_used.append('Action News 5')
    
    # East TN - WVLT (Gray)
    print("\n--- WVLT (East TN) ---")
    wvlt = scrape_gray_media(WVLT_URL, 'WVLT')
    if wvlt:
        all_closings.extend(wvlt)
        sources_used.append('WVLT')
    
    # Deduplicate
    all_closings = deduplicate_closings(all_closings)
    
    # Stats
    by_status = {}
    by_region = {}
    for c in all_closings:
        by_status[c['status']] = by_status.get(c['status'], 0) + 1
        by_region[c['region']] = by_region.get(c['region'], 0) + 1
    
    # Output
    output = {
        'meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_closings': len(all_closings),
            'by_status': by_status,
            'by_region': by_region,
            'sources': sources_used
        },
        'closings': all_closings
    }
    
    with open('closings.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Total: {len(all_closings)} closings")
    print(f"By status: {by_status}")
    print(f"By region: {by_region}")
    print(f"Sources: {sources_used}")
    print("Written to closings.json")
    
    others = [c['name'] for c in all_closings if c['region'] == 'Other']
    if others:
        print(f"\nUnmapped (Other): {others}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
