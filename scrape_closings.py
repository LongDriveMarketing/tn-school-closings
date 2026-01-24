#!/usr/bin/env python3
"""
Tennessee School Closings Scraper
Aggregates school closing data from multiple TN news sources
For The Tennessee Firefly - https://tnfirefly.com
"""

import json
import re
import os
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

# Output paths
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', './data')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'closings.json')

# News sources to scrape
SOURCES = {
    'newschannel5': {
        'name': 'NewsChannel 5 Nashville',
        'url': 'https://www.newschannel5.com/weather/school-closings-delays',
        'region': 'Middle Tennessee'
    },
    'wkrn': {
        'name': 'WKRN News 2',
        'url': 'https://www.wkrn.com/weather/closings/',
        'region': 'Middle Tennessee'
    },
    'wbbj': {
        'name': 'WBBJ-TV',
        'url': 'https://www.wbbjtv.com/weather/school-closings/',
        'region': 'West Tennessee'
    },
    'wjhl': {
        'name': 'WJHL Tri-Cities',
        'url': 'https://www.wjhl.com/weather/closings/',
        'region': 'East Tennessee'
    },
    'local3': {
        'name': 'Local 3 News Chattanooga',
        'url': 'https://www.local3news.com/local-weather/school-closings/',
        'region': 'East Tennessee'
    },
    'wreg': {
        'name': 'WREG Memphis',
        'url': 'https://wreg.com/weather/closings/',
        'region': 'West Tennessee'
    }
}

# Status normalization
STATUS_PATTERNS = {
    'CLOSED': [r'closed', r'closing$', r'no school'],
    'DELAYED': [r'delay', r'delayed', r'late start', r'hour delay'],
    'EARLY_DISMISSAL': [r'early', r'dismissal', r'closing at', r'releasing'],
    'REMOTE': [r'remote', r'virtual', r'nti', r'online'],
    'MODIFIED': [r'modified', r'adjusted']
}


class NewsChannel5Parser(HTMLParser):
    """Parser specifically for NewsChannel 5's closings page structure"""
    
    def __init__(self):
        super().__init__()
        self.closings = []
        self.in_closing_item = False
        self.current_name = None
        self.current_status = None
        self.capture_text = False
        self.text_buffer = ''
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        # NewsChannel 5 uses specific class patterns for closings
        if 'class' in attrs_dict:
            classes = attrs_dict['class']
            if 'closing' in classes.lower() or 'delay' in classes.lower():
                self.in_closing_item = True
                self.capture_text = True
                
    def handle_endtag(self, tag):
        if self.in_closing_item and tag in ['div', 'li', 'tr']:
            if self.text_buffer.strip():
                self._parse_closing_text(self.text_buffer.strip())
            self.in_closing_item = False
            self.capture_text = False
            self.text_buffer = ''
            
    def handle_data(self, data):
        if self.capture_text:
            self.text_buffer += ' ' + data
            
    def _parse_closing_text(self, text):
        # Try to extract name and status from text
        text = ' '.join(text.split())  # Normalize whitespace
        
        # Common patterns: "District Name - CLOSED" or "District Name DELAYED 2 HOURS"
        for status, patterns in STATUS_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Extract the name (everything before the status)
                    name = re.split(pattern, text, flags=re.IGNORECASE)[0].strip()
                    name = re.sub(r'[-–—:]$', '', name).strip()
                    
                    # Get the full status text
                    status_match = re.search(rf'({pattern}.*?)$', text, re.IGNORECASE)
                    status_text = status_match.group(1) if status_match else status
                    
                    if name and len(name) > 2:
                        self.closings.append({
                            'name': name,
                            'status': status,
                            'status_detail': status_text.strip(),
                            'raw_text': text
                        })
                    return


class GenericClosingsParser(HTMLParser):
    """Generic parser that looks for common closing patterns in HTML"""
    
    def __init__(self):
        super().__init__()
        self.closings = []
        self.all_text = []
        self.in_body = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.in_body = True
            
    def handle_endtag(self, tag):
        if tag == 'body':
            self.in_body = False
            
    def handle_data(self, data):
        if self.in_body:
            text = data.strip()
            if text and len(text) > 3:
                self.all_text.append(text)
                
    def extract_closings(self):
        """Process collected text to find closings"""
        full_text = ' '.join(self.all_text)
        
        # Look for patterns like "County Schools - CLOSED" or "School District: 2 hour delay"
        patterns = [
            r'([A-Z][a-zA-Z\s]+(?:Schools?|District|Academy|County|University|College))\s*[-–:]\s*(closed|delayed?|early|2\s*hour|virtual|remote)',
            r'([A-Z][a-zA-Z\s]+(?:Schools?|District|Academy|County))\s+(closed|is\s+closed|will\s+be\s+closed)',
            r'([A-Z][a-zA-Z\s]+)\s*[-–]\s*(CLOSED|DELAYED|CLOSING)',
        ]
        
        seen = set()
        for pattern in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                status_text = match.group(2).strip()
                
                # Normalize status
                status = 'CLOSED'
                for s, pats in STATUS_PATTERNS.items():
                    for p in pats:
                        if re.search(p, status_text, re.IGNORECASE):
                            status = s
                            break
                
                key = name.lower()
                if key not in seen and len(name) > 5:
                    seen.add(key)
                    self.closings.append({
                        'name': name,
                        'status': status,
                        'status_detail': status_text,
                        'raw_text': match.group(0)
                    })
        
        return self.closings


def fetch_url(url, timeout=30):
    """Fetch URL content with proper headers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; TNFireflyBot/1.0; +https://tnfirefly.com)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except (URLError, HTTPError) as e:
        print(f"Error fetching {url}: {e}")
        return None


def scrape_newschannel5():
    """Scrape NewsChannel 5 Nashville"""
    html = fetch_url(SOURCES['newschannel5']['url'])
    if not html:
        return []
    
    # NewsChannel 5 has a specific structure - look for closing entries
    closings = []
    
    # They list closings in a specific format with county/district names
    # Pattern: Name followed by status on same or next line
    lines = html.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for lines that look like school/county names followed by status
        for status, patterns in STATUS_PATTERNS.items():
            for pattern in patterns:
                match = re.search(rf'^([A-Za-z\s]+)\s*\n?\s*({pattern}.*?)$', line, re.IGNORECASE | re.MULTILINE)
                if match:
                    name = match.group(1).strip()
                    status_text = match.group(2).strip()
                    if len(name) > 3:
                        closings.append({
                            'name': name,
                            'status': status,
                            'status_detail': status_text,
                            'source': 'newschannel5'
                        })
    
    # Also try the generic parser
    parser = GenericClosingsParser()
    parser.feed(html)
    generic_closings = parser.extract_closings()
    
    # Merge, preferring specific matches
    seen = {c['name'].lower() for c in closings}
    for c in generic_closings:
        if c['name'].lower() not in seen:
            c['source'] = 'newschannel5'
            closings.append(c)
    
    return closings


def scrape_generic(source_key):
    """Generic scraper for other news sources"""
    source = SOURCES[source_key]
    html = fetch_url(source['url'])
    if not html:
        return []
    
    parser = GenericClosingsParser()
    parser.feed(html)
    closings = parser.extract_closings()
    
    for c in closings:
        c['source'] = source_key
        c['region'] = source['region']
    
    return closings


def normalize_name(name):
    """Normalize school/district names for deduplication"""
    name = name.lower().strip()
    # Remove common suffixes
    name = re.sub(r'\s*(school district|schools|county schools|city schools|school)$', '', name)
    # Normalize whitespace
    name = ' '.join(name.split())
    return name


def merge_closings(all_closings):
    """Merge closings from multiple sources, deduplicating"""
    merged = {}
    
    for closing in all_closings:
        key = normalize_name(closing['name'])
        
        if key not in merged:
            merged[key] = {
                'id': key.replace(' ', '-'),
                'name': closing['name'],
                'status': closing['status'],
                'status_detail': closing.get('status_detail', closing['status']),
                'sources': [closing.get('source', 'unknown')],
                'region': closing.get('region', 'Tennessee'),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            # Add source if not already listed
            if closing.get('source') not in merged[key]['sources']:
                merged[key]['sources'].append(closing.get('source', 'unknown'))
            # Update status if this source has more detail
            if len(closing.get('status_detail', '')) > len(merged[key].get('status_detail', '')):
                merged[key]['status_detail'] = closing['status_detail']
    
    return list(merged.values())


def main():
    """Main scraping function"""
    print(f"Starting Tennessee School Closings scrape at {datetime.now(timezone.utc).isoformat()}")
    
    all_closings = []
    
    # Scrape each source
    for source_key in SOURCES:
        print(f"Scraping {SOURCES[source_key]['name']}...")
        try:
            if source_key == 'newschannel5':
                closings = scrape_newschannel5()
            else:
                closings = scrape_generic(source_key)
            
            print(f"  Found {len(closings)} closings")
            all_closings.extend(closings)
        except Exception as e:
            print(f"  Error: {e}")
    
    # Merge and deduplicate
    merged = merge_closings(all_closings)
    print(f"\nTotal unique closings: {len(merged)}")
    
    # Build output data
    output = {
        'meta': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'sources': list(SOURCES.keys()),
            'total_closings': len(merged),
            'by_region': {},
            'by_status': {}
        },
        'closings': sorted(merged, key=lambda x: x['name'])
    }
    
    # Calculate stats
    for closing in merged:
        region = closing.get('region', 'Unknown')
        status = closing.get('status', 'Unknown')
        
        output['meta']['by_region'][region] = output['meta']['by_region'].get(region, 0) + 1
        output['meta']['by_status'][status] = output['meta']['by_status'].get(status, 0) + 1
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nOutput written to {OUTPUT_FILE}")
    
    # Also print summary
    print("\n=== SUMMARY ===")
    print(f"Total: {len(merged)} closings")
    for region, count in output['meta']['by_region'].items():
        print(f"  {region}: {count}")
    print("\nBy Status:")
    for status, count in output['meta']['by_status'].items():
        print(f"  {status}: {count}")
    
    return output


if __name__ == '__main__':
    main()
