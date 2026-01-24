#!/usr/bin/env python3
"""
Tennessee School Closings Scraper
Scrapes NewsChannel 5's school closings page - data is server-rendered HTML

District-to-region mappings extracted from official TN school data.
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
    'Connection': 'keep-alive',
}

# =============================================================================
# REGION MAPPINGS - Extracted from TN School Data (schoolData.js)
# Organized by Grand Division per TCA 4-1-201 through 4-1-204
# =============================================================================

# All districts mapped to their region based on county location
DISTRICT_TO_REGION = {
    # -------------------------------------------------------------------------
    # EAST TENNESSEE
    # -------------------------------------------------------------------------
    # Anderson County
    "Anderson County Schools": "East Tennessee",
    "Clinton City Schools": "East Tennessee",
    "Oak Ridge City Schools": "East Tennessee",
    # Bledsoe County
    "Bledsoe County Schools": "East Tennessee",
    # Blount County
    "Alcoa City Schools": "East Tennessee",
    "Blount County Schools": "East Tennessee",
    "Maryville City Schools": "East Tennessee",
    # Bradley County
    "Bradley County Schools": "East Tennessee",
    "Cleveland City Schools": "East Tennessee",
    # Campbell County
    "Campbell County Schools": "East Tennessee",
    # Carter County
    "Carter County Schools": "East Tennessee",
    "Elizabethton City Schools": "East Tennessee",
    # Claiborne County
    "Claiborne County Schools": "East Tennessee",
    # Cocke County
    "Cocke County Schools": "East Tennessee",
    "Newport City Elementary Schools": "East Tennessee",
    "Newport City Schools": "East Tennessee",
    # Cumberland County
    "Cumberland County Schools": "East Tennessee",
    # Grainger County
    "Grainger County Schools": "East Tennessee",
    # Greene County
    "Greene County Schools": "East Tennessee",
    "Greeneville City Schools": "East Tennessee",
    # Hamblen County
    "Hamblen County Schools": "East Tennessee",
    "Morristown City Schools": "East Tennessee",
    # Hamilton County
    "Hamilton County Schools": "East Tennessee",
    "Hamilton County Department of Education": "East Tennessee",
    # Hancock County
    "Hancock County Schools": "East Tennessee",
    # Hawkins County
    "Hawkins County Schools": "East Tennessee",
    "Rogersville City Schools": "East Tennessee",
    # Jefferson County
    "Jefferson County Schools": "East Tennessee",
    # Johnson County
    "Johnson County Schools": "East Tennessee",
    # Knox County
    "Knox County Schools": "East Tennessee",
    # Loudon County
    "Loudon County Schools": "East Tennessee",
    "Lenoir City Schools": "East Tennessee",
    # Marion County
    "Marion County Schools": "East Tennessee",
    # McMinn County
    "McMinn County Schools": "East Tennessee",
    "Athens City Schools": "East Tennessee",
    "Etowah City Schools": "East Tennessee",
    # Meigs County
    "Meigs County Schools": "East Tennessee",
    # Monroe County
    "Monroe County Schools": "East Tennessee",
    "Sweetwater City Schools": "East Tennessee",
    # Morgan County
    "Morgan County Schools": "East Tennessee",
    # Polk County
    "Polk County Schools": "East Tennessee",
    # Rhea County
    "Rhea County Schools": "East Tennessee",
    "Dayton City Schools": "East Tennessee",
    # Roane County
    "Roane County Schools": "East Tennessee",
    # Scott County
    "Scott County Schools": "East Tennessee",
    # Sevier County
    "Sevier County Schools": "East Tennessee",
    # Sullivan County
    "Sullivan County Schools": "East Tennessee",
    "Bristol Tennessee City Schools": "East Tennessee",
    "Bristol City Schools": "East Tennessee",
    "Kingsport City Schools": "East Tennessee",
    # Unicoi County
    "Unicoi County Schools": "East Tennessee",
    # Union County
    "Union County Schools": "East Tennessee",
    # Washington County
    "Washington County Schools": "East Tennessee",
    "Johnson City Schools": "East Tennessee",
    
    # -------------------------------------------------------------------------
    # MIDDLE TENNESSEE
    # -------------------------------------------------------------------------
    # Bedford County
    "Bedford County Schools": "Middle Tennessee",
    # Cannon County
    "Cannon County Schools": "Middle Tennessee",
    # Cheatham County
    "Cheatham County Schools": "Middle Tennessee",
    # Clay County
    "Clay County Schools": "Middle Tennessee",
    # Coffee County
    "Coffee County Schools": "Middle Tennessee",
    "Manchester City Schools": "Middle Tennessee",
    "Tullahoma City Schools": "Middle Tennessee",
    # Davidson County
    "Achievement School District": "Middle Tennessee",
    "Metropolitan Nashville Public Schools": "Middle Tennessee",
    "Metro Nashville Public Schools": "Middle Tennessee",
    "MNPS": "Middle Tennessee",
    "Tennessee Public Charter School Commission": "Middle Tennessee",
    # DeKalb County
    "Dekalb County Schools": "Middle Tennessee",
    "DeKalb County Schools": "Middle Tennessee",
    # Dickson County
    "Dickson County Schools": "Middle Tennessee",
    # Fentress County
    "Fentress County Schools": "Middle Tennessee",
    "Alvin C. York Agricultural Institute": "Middle Tennessee",
    # Franklin County
    "Franklin County Schools": "Middle Tennessee",
    # Giles County
    "Giles County Schools": "Middle Tennessee",
    # Grundy County
    "Grundy County Schools": "Middle Tennessee",
    # Hickman County
    "Hickman County Schools": "Middle Tennessee",
    # Houston County
    "Houston County Schools": "Middle Tennessee",
    # Humphreys County
    "Humphreys County Schools": "Middle Tennessee",
    # Jackson County
    "Jackson County Schools": "Middle Tennessee",
    # Lawrence County
    "Lawrence County Schools": "Middle Tennessee",
    # Lewis County
    "Lewis County Schools": "Middle Tennessee",
    # Lincoln County
    "Lincoln County Schools": "Middle Tennessee",
    "Fayetteville City Schools": "Middle Tennessee",
    # Macon County
    "Macon County Schools": "Middle Tennessee",
    # Marshall County
    "Marshall County Schools": "Middle Tennessee",
    # Maury County
    "Maury County Schools": "Middle Tennessee",
    "Maury County Public Schools": "Middle Tennessee",
    "Columbia City Schools": "Middle Tennessee",
    # Montgomery County
    "Montgomery County Schools": "Middle Tennessee",
    "Clarksville-Montgomery County Schools": "Middle Tennessee",
    "Clarksville-Montgomery County School System": "Middle Tennessee",
    "CMCSS": "Middle Tennessee",
    # Moore County
    "Moore County Schools": "Middle Tennessee",
    # Overton County
    "Overton County Schools": "Middle Tennessee",
    # Perry County
    "Perry County Schools": "Middle Tennessee",
    # Pickett County
    "Pickett County Schools": "Middle Tennessee",
    # Putnam County
    "Putnam County Schools": "Middle Tennessee",
    "Putnam County School System": "Middle Tennessee",
    # Robertson County
    "Robertson County Schools": "Middle Tennessee",
    # Rutherford County
    "Rutherford County Schools": "Middle Tennessee",
    "Murfreesboro City Schools": "Middle Tennessee",
    # Sequatchie County
    "Sequatchie County Schools": "Middle Tennessee",
    # Smith County
    "Smith County Schools": "Middle Tennessee",
    # Stewart County
    "Stewart County Schools": "Middle Tennessee",
    # Sumner County
    "Sumner County Schools": "Middle Tennessee",
    # Trousdale County
    "Trousdale County Schools": "Middle Tennessee",
    # Van Buren County
    "Van Buren County Schools": "Middle Tennessee",
    # Warren County
    "Warren County Schools": "Middle Tennessee",
    # Wayne County
    "Wayne County Schools": "Middle Tennessee",
    # White County
    "White County Schools": "Middle Tennessee",
    # Williamson County
    "Williamson County Schools": "Middle Tennessee",
    "Franklin Special School District": "Middle Tennessee",
    # Wilson County
    "Wilson County Schools": "Middle Tennessee",
    "Lebanon Special School District": "Middle Tennessee",
    
    # -------------------------------------------------------------------------
    # WEST TENNESSEE
    # -------------------------------------------------------------------------
    # Benton County
    "Benton County Schools": "West Tennessee",
    # Carroll County
    "Hollow Rock-Bruceton Special School District": "West Tennessee",
    "Huntingdon Special Schools": "West Tennessee",
    "McKenzie Special School District": "West Tennessee",
    "South Carroll Special School District": "West Tennessee",
    "West Carroll Special School District": "West Tennessee",
    # Chester County
    "Chester County Schools": "West Tennessee",
    # Crockett County
    "Alamo City Schools": "West Tennessee",
    "Bells City Schools": "West Tennessee",
    "Crockett County Schools": "West Tennessee",
    # Decatur County
    "Decatur County Schools": "West Tennessee",
    # Dyer County
    "Dyer County Schools": "West Tennessee",
    "Dyersburg City Schools": "West Tennessee",
    # Fayette County
    "Fayette County Schools": "West Tennessee",
    # Gibson County
    "Bradford Special Schools": "West Tennessee",
    "Gibson County Special School District": "West Tennessee",
    "Humboldt City Schools": "West Tennessee",
    "Milan Special School District": "West Tennessee",
    "Trenton City Schools": "West Tennessee",
    # Hardeman County
    "Hardeman County Schools": "West Tennessee",
    # Hardin County
    "Hardin County Schools": "West Tennessee",
    # Haywood County
    "Haywood County Schools": "West Tennessee",
    # Henderson County
    "Henderson County Schools": "West Tennessee",
    "Lexington City Schools": "West Tennessee",
    # Henry County
    "Henry County Schools": "West Tennessee",
    "Paris Special School District": "West Tennessee",
    # Lake County
    "Lake County Schools": "West Tennessee",
    # Lauderdale County
    "Lauderdale County Schools": "West Tennessee",
    # Madison County
    "Madison County Schools": "West Tennessee",
    "Jackson-Madison County Schools": "West Tennessee",
    "Jackson-Madison County School System": "West Tennessee",
    # McNairy County
    "McNairy County Schools": "West Tennessee",
    # Obion County
    "Obion County Schools": "West Tennessee",
    "Union City Schools": "West Tennessee",
    # Shelby County
    "Shelby County Schools": "West Tennessee",
    "Memphis-Shelby County Schools": "West Tennessee",
    "Arlington Community Schools": "West Tennessee",
    "Bartlett City Schools": "West Tennessee",
    "Collierville Schools": "West Tennessee",
    "Germantown Municipal School District": "West Tennessee",
    "Lakeland School System": "West Tennessee",
    "Millington Municipal Schools": "West Tennessee",
    # Tipton County
    "Tipton County Schools": "West Tennessee",
    "Covington City Schools": "West Tennessee",
    # Weakley County
    "Weakley County Schools": "West Tennessee",
}

# County name to region (fallback for pattern matching)
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
}

# City keywords for fuzzy matching (last resort)
CITY_REGIONS = {
    # East TN cities
    "Knoxville": "East Tennessee", "Chattanooga": "East Tennessee", "Johnson City": "East Tennessee",
    "Kingsport": "East Tennessee", "Bristol": "East Tennessee", "Morristown": "East Tennessee",
    "Cleveland": "East Tennessee", "Maryville": "East Tennessee", "Oak Ridge": "East Tennessee",
    "Athens": "East Tennessee", "Greeneville": "East Tennessee", "Elizabethton": "East Tennessee",
    "Sevierville": "East Tennessee", "Pigeon Forge": "East Tennessee", "Gatlinburg": "East Tennessee",
    # Middle TN cities
    "Nashville": "Middle Tennessee", "Murfreesboro": "Middle Tennessee", "Franklin": "Middle Tennessee",
    "Clarksville": "Middle Tennessee", "Columbia": "Middle Tennessee", "Gallatin": "Middle Tennessee",
    "Hendersonville": "Middle Tennessee", "Lebanon": "Middle Tennessee", "Cookeville": "Middle Tennessee",
    "Shelbyville": "Middle Tennessee", "Tullahoma": "Middle Tennessee", "Manchester": "Middle Tennessee",
    "Dickson": "Middle Tennessee", "Springfield": "Middle Tennessee", "Portland": "Middle Tennessee",
    "Smyrna": "Middle Tennessee", "La Vergne": "Middle Tennessee", "Spring Hill": "Middle Tennessee",
    "Goodlettsville": "Middle Tennessee", "White House": "Middle Tennessee", "McMinnville": "Middle Tennessee",
    "Lawrenceburg": "Middle Tennessee", "Pulaski": "Middle Tennessee", "Fayetteville": "Middle Tennessee",
    "Lewisburg": "Middle Tennessee", "Sparta": "Middle Tennessee", "Crossville": "Middle Tennessee",
    # West TN cities
    "Memphis": "West Tennessee", "Jackson": "West Tennessee", "Bartlett": "West Tennessee",
    "Collierville": "West Tennessee", "Germantown": "West Tennessee", "Dyersburg": "West Tennessee",
    "Millington": "West Tennessee", "Covington": "West Tennessee", "Ripley": "West Tennessee",
    "Savannah": "West Tennessee", "Selmer": "West Tennessee", "Bolivar": "West Tennessee",
    "Lexington": "West Tennessee", "Henderson": "West Tennessee", "Humboldt": "West Tennessee",
    "Milan": "West Tennessee", "Trenton": "West Tennessee", "Union City": "West Tennessee",
    "Paris": "West Tennessee", "Martin": "West Tennessee", "McKenzie": "West Tennessee",
}


def classify_region(name):
    """
    Classify school/district into TN region.
    Priority: exact district match > county in name > city keyword > Other
    """
    name_clean = name.strip()
    name_upper = name_clean.upper()
    
    # 1. Exact district match
    if name_clean in DISTRICT_TO_REGION:
        return DISTRICT_TO_REGION[name_clean]
    
    # 2. Partial district match (handles variations like "Williamson Co Schools")
    for district, region in DISTRICT_TO_REGION.items():
        district_upper = district.upper()
        # Check if district name is contained in the closing name
        if district_upper in name_upper:
            return region
        # Check if closing name is contained in district (for abbreviations)
        if len(name_clean) > 5 and name_upper in district_upper:
            return region
    
    # 3. County name in the closing name
    for county, region in COUNTY_REGIONS.items():
        if county.upper() in name_upper:
            return region
    
    # 4. City keyword match
    for city, region in CITY_REGIONS.items():
        if city.upper() in name_upper:
            return region
    
    # 5. No match found
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
    print("=" * 60)
    print("TN SCHOOL CLOSINGS SCRAPER")
    print(f"Run time: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
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
    
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Total: {len(closings)} closings")
    print(f"By status: {by_status}")
    print(f"By region: {by_region}")
    print("Written to closings.json")
    
    # List any "Other" regions for debugging
    others = [c['name'] for c in closings if c['region'] == 'Other']
    if others:
        print(f"\nUnmapped (Other): {others}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
