# Tennessee School Closings System

**Live school closings aggregator for The Tennessee Firefly**

This system scrapes school closing data from multiple Tennessee news sources and publishes it as a unified, searchable page.

## 🔥 Features

- **Statewide Coverage**: Pulls from NewsChannel 5 (Nashville), WKRN, WBBJ (West TN), WJHL (Tri-Cities), Local 3 (Chattanooga), WREG (Memphis)
- **Auto-Updates**: GitHub Actions runs every 30 minutes during school hours
- **Billy Badass UI**: Dark theme, mobile-first, real-time feel
- **Smart Deduplication**: Merges data from multiple sources
- **Newsletter Ready**: JSON output for Campaign Monitor integration

## 📁 Structure

```
tn-school-closings/
├── .github/
│   └── workflows/
│       └── scrape.yml       # GitHub Actions workflow
├── scraper/
│   └── scrape_closings.py   # Main scraper script
├── page/
│   └── school-closings.html # Frontend page for TNFirefly
├── data/
│   └── closings.json        # Output data (auto-generated)
└── README.md
```

## 🚀 Setup

### 1. Create GitHub Repository

```bash
# Create new repo on GitHub: tn-school-closings
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/tn-school-closings.git
git push -u origin main
```

### 2. Enable GitHub Actions

- Go to repo Settings → Actions → General
- Enable "Read and write permissions" under Workflow permissions

### 3. Update Data URL in Frontend

Edit `page/school-closings.html` and replace:
```javascript
const DATA_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/tn-school-closings/main/data/closings.json';
```

With your actual GitHub username.

### 4. Add to Squarespace

**Option A: Code Block (simplest)**
1. Add a Code Block to your TNFirefly page
2. Paste the contents of `page/school-closings.html`

**Option B: Embed via iframe**
1. Host the HTML file (GitHub Pages, Netlify, etc.)
2. Add via Embed Block: `<iframe src="YOUR_URL" width="100%" height="800px"></iframe>`

**Option C: Code Injection (recommended)**
1. Copy the `<style>` contents to Design → Custom CSS
2. Copy the HTML structure to a Code Block
3. Copy the `<script>` to Settings → Advanced → Code Injection → Footer

## 📧 Newsletter Integration (Campaign Monitor)

### JSON Feed URL
```
https://raw.githubusercontent.com/YOUR_USERNAME/tn-school-closings/main/data/closings.json
```

### Sample Data Structure
```json
{
  "meta": {
    "generated_at": "2026-01-24T12:00:00Z",
    "total_closings": 15,
    "by_region": {
      "Middle Tennessee": 8,
      "East Tennessee": 4,
      "West Tennessee": 3
    },
    "by_status": {
      "CLOSED": 10,
      "DELAYED": 5
    }
  },
  "closings": [
    {
      "id": "davidson-county",
      "name": "Davidson County Schools",
      "status": "CLOSED",
      "status_detail": "CLOSED - All day",
      "region": "Middle Tennessee",
      "sources": ["newschannel5", "wkrn"],
      "updated_at": "2026-01-24T06:00:00Z"
    }
  ]
}
```

### Campaign Monitor RSS-to-Email

You can set up a triggered campaign that sends when `meta.total_closings > 0`:

1. Create a new Triggered Campaign
2. Use the JSON feed as data source
3. Template example:

```html
<h1>🚨 Tennessee School Closings Alert</h1>
<p>{{meta.total_closings}} schools are closed or delayed.</p>

{{#each closings}}
<div style="padding: 10px; margin: 5px 0; background: #f5f5f5;">
  <strong>{{name}}</strong>
  <span style="color: red;">{{status}}</span>
</div>
{{/each}}

<p><a href="https://tnfirefly.com/school-closings">View Full List →</a></p>
```

## 🔧 Manual Testing

```bash
# Run scraper locally
cd scraper
python scrape_closings.py

# Check output
cat data/closings.json | jq .
```

## 📊 Status Codes

| Status | Description |
|--------|-------------|
| `CLOSED` | School fully closed |
| `DELAYED` | Delayed start (1hr, 2hr, etc.) |
| `EARLY_DISMISSAL` | Closing early |
| `REMOTE` | Virtual/NTI day |
| `MODIFIED` | Modified schedule |

## 🐛 Troubleshooting

**Scraper returns empty data:**
- News sites may block automated requests
- Check if source URLs have changed
- Run manually with `python scrape_closings.py` to see errors

**GitHub Actions not running:**
- Check Actions tab for errors
- Ensure workflow file is in `.github/workflows/`
- Verify repository permissions

**Data not updating on page:**
- Raw GitHub URLs can be cached for ~5 minutes
- Hard refresh the page (Ctrl+Shift+R)
- Check browser console for fetch errors

## 📝 Adding More Sources

Edit `scraper/scrape_closings.py` and add to the `SOURCES` dict:

```python
SOURCES = {
    # ... existing sources ...
    'new_station': {
        'name': 'New Station Name',
        'url': 'https://newstation.com/closings/',
        'region': 'Region Name'
    }
}
```

Then implement a scraper function if the generic one doesn't work.

## 📄 License

MIT - Built for The Tennessee Firefly

---

**Questions?** Contact Long Drive Marketing
